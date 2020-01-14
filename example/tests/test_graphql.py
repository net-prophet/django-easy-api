import itertools
import json
import random

from django.contrib.auth import get_user_model
from django.test import modify_settings
from rest_framework import status
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.test import APIClient, APITestCase
from graphql_relay import from_global_id, to_global_id

from unittest import skip
from example.app.widgets.models import Store, Widget, default_store_id
from example.app.widgets.options import COLORS, SHAPES, SIZES

User = get_user_model()

TEST = {"username": "testuser", "email": "test@test.co", "password": "testing123"}

SUPER = {"username": "testsuper", "email": "super@test.co", "password": "super123"}
PUBLIC = "/publicapi/graphql"
PRIVATE = "/privateapi/graphql"
ADMIN = "/complexapi/graphql"

NUM_WIDGETS = 30


class GraphQLMethodsTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @classmethod
    def setUpClass(self):
        self.maxDiff = 30 * 1000
        # Set up the DB
        super(GraphQLMethodsTest, self).setUpClass()
        for color, size, shape in random.choices(
            list(itertools.product(COLORS, SIZES, SHAPES)), k=NUM_WIDGETS
        ):
            Widget.objects.create(color=color[0], size=size[0], shape=shape[0], store_id=default_store_id())

        # Let's create a test user and set our client
        self.user = User.objects.create(username=TEST["username"], email=TEST["email"])
        self.user.set_password(TEST["password"])
        self.user.save()

        # Also, a superuser
        self.suser = User.objects.create_superuser(
            username=SUPER["username"], email=SUPER["email"], password=SUPER["password"]
        )
        self.suser.save()

    def gql(
        self, target, query, user=None, assert_code=status.HTTP_200_OK, message=None
    ):
        if user:
            self.client.login(username=user["username"], password=user["password"])

        response = self.client.post(target, data={"query": query})

        if assert_code:
            self.assertEqual(
                response.status_code,
                assert_code,
                message or "Unexpected graphql response, expected %s" % assert_code,
            )

        if assert_code == status.HTTP_200_OK:
            return json.loads(response.content.decode("utf-8"))
        else:
            return response

    def test_public_root(self):
        schema = self.gql(PUBLIC, "{ __schema { __typename } }")
        self.assertEqual(schema, {"data": {"__schema": {"__typename": "__Schema"}}})

    def test_public_list_stores(self):
        stores = self.gql(PUBLIC, "{ allStores { edges { node { name } } } }")
        self.assertEqual(
            stores, {"data": {"allStores": {"edges": [{"node": {"name": "DEFAULT"}}]}}}
        )

        self.gql(
            PUBLIC,
            "{ allStores { edges { node { name, owner { username } } } } }",
            assert_code=status.HTTP_400_BAD_REQUEST,
            message="Shouldn't be able to see private fields",
        )

    def test_public_list_stores_with_widgets(self):
        with_widgets = self.gql(
            PUBLIC,
            "{ allStores { edges { node { name, widgets { edges { node { name } } } } } } }",
        )
        edges = with_widgets["data"]["allStores"]["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(len(edges[0]["node"]["widgets"]["edges"]), NUM_WIDGETS)

    def test_private_list_stores(self):
        # Admin owns the stores
        Store.objects.update(owner=self.suser)
        # TEST cant see anything
        stores = self.gql(
            PRIVATE,
            "{ allStores { edges { node { name, owner {username} } } } }",
            user=TEST,
        )
        self.assertEqual(stores, {"data": {"allStores": {"edges": []}}})

        Store.objects.update(owner=self.user)
        # Now TEST owns the store and can see the private fields
        stores = self.gql(
            PRIVATE,
            "{ allStores { edges { node { name, owner {username} } } } }",
            user=TEST,
        )
        self.assertEqual(
            stores,
            {
                "data": {
                    "allStores": {
                        "edges": [
                            {
                                "node": {
                                    "name": "DEFAULT",
                                    "owner": {"username": TEST["username"]},
                                }
                            }
                        ]
                    }
                }
            },
        )

    # Permissions to create and delete a widget are store owner only
    def test_create_and_delete_widget(self):
        Store.objects.update(owner=self.user)
        stores = self.gql(PRIVATE, "{ allStores { edges { node { id } } } }", user=TEST)
        store_id = stores["data"]["allStores"]["edges"][0]["node"]["id"]
        created = self.gql(
            PRIVATE,
            """
            mutation { 
                createWidget(input: {
                    name: "test",
                    size: "small",
                    shape: "circle",
                    color: "blue",
                    store: "%s"
                }) { name, id, size, shape, color, store }
            }"""
            % store_id,
            user=TEST,
        )
        print(created)
        widget = created["data"]["createWidget"]
        id = widget.pop("id")
        self.assertEqual(
            widget,
            {
                "name": "test",
                "size": "small",
                "shape": "circle",
                "color": "blue",
                "store": from_global_id(store_id)[1],
            },
        )
        raise

        # Now lets make sure being authenticated isn't enough
        self.client.login(username=TEST["username"], password=TEST["password"])
        widgets = self.client.get("/complexapi/widgets/")
        self.assertEqual(widgets.status_code, status.HTTP_403_FORBIDDEN)

        create = {
            "name": "test_widget",
            "color": "blue",
            "size": "large",
            "shape": "circle",
        }
        response = self.client.post("/complexapi/widgets/", data=create)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Finally, a superuser should be successful
        self.client.login(username=SUPER["username"], password=SUPER["password"])
        response = self.client.post("/complexapi/widgets/", data=create)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Let's retrieve it with our filters
        filtered = self.client.get("/complexapi/widgets/?name=test_widget")
        for k, v in create.items():
            self.assertEqual(filtered.data[0][k], v)

        # Let's check that we can retrieve what we just created
        pk = response.data["pk"]
        url = "/complexapi/widgets/%s/" % str(pk)
        delete_me = self.client.get(url)
        for k, v in create.items():
            self.assertEqual(delete_me.data[k], v)

        # Delete it
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

        # Check if its deleted
        deleted = self.client.delete(url)
        self.assertEqual(deleted.status_code, status.HTTP_404_NOT_FOUND)

        # Check if its deleted via filter
        filtered_del = self.client.get("/complexapi/widgets/?name=test_widget")
        self.assertEqual(filtered_del.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered_del.data, [])

