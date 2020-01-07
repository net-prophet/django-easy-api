from django.db import models
from .options import COLORS, SIZES, SHAPES


class Widget(models.Model):
    name = models.CharField(max_length=30, blank=True)
    color = models.CharField(choices=COLORS, max_length=30)
    size = models.CharField(choices=SIZES, max_length=30)
    shape = models.CharField(choices=SHAPES, max_length=30)
    cost = models.FloatField(default=0,
                             blank=True)

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    def get_size(self):
        return self.size

    def get_shape(self):
        return self.shape

    def get_cost(self):
        return self.cost

    def save(self, *args, **kwargs):
        if self.name == '':
            self.name = '%s.%s.%s' % (self.color, self.size, self.shape)

        color_sum = sum([ord(x) for x in self.color])
        size_sum = sum([ord(x) for x in self.size])
        shape_sum = sum([ord(x) for x in self.shape])
        self.cost = color_sum + size_sum + shape_sum
        super(Widget, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
