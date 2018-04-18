# socialauth/views.py
from django.views.generic import TemplateView
from django.shortcuts import render

class HomePageView(TemplateView):
    template_name = 'home.html'
    def get_context_data(self, **kwargs):
        context_data = super(HomePageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'home'
        return context_data

class SocialPageView(TemplateView):
    template_name = "social.html"
    def get_context_data(self, **kwargs):
        context_data = super(SocialPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'social'
        return context_data

class ContactPageView(TemplateView):
    template_name = "contact.html"
    def get_context_data(self, **kwargs):
        context_data = super(ContactPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'contact'
        return context_data

class ResultsPageView(TemplateView):
    template_name = "results.html"
    def get_context_data(self, **kwargs):
        context_data = super(ResultsPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'results'
        return context_data
