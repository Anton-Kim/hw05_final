from django.views.generic.base import TemplateView


class About_author(TemplateView):
    template_name = 'about/about_author.html'


class About_tech(TemplateView):
    template_name = 'about/about_tech.html'
