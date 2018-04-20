# socialauth/views.py
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseNotFound, Http404,  HttpResponseRedirect

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

class GooglePageView(TemplateView):
    template_name = "google_share.html"
    def get_context_data(self, **kwargs):
        context_data = super(GooglePageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'share_google'
        return context_data

class SocialConnectionsPageView(TemplateView):
    template_name = "social_connections.html"
    def get_context_data(self, **kwargs):
        context_data = super(SocialConnectionsPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'social_connections'
        return context_data

class HowItWorksPageView(TemplateView):
    template_name = "tool.html"
    def get_context_data(self, **kwargs):
        context_data = super(HowItWorksPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'howitworks'
        return context_data

class AboutPageView(TemplateView):
    template_name = "about.html"
    def get_context_data(self, **kwargs):
        context_data = super(AboutPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'about_research'
        return context_data

class PrivacyPageView(TemplateView):
    template_name = "privacy.html"
    def get_context_data(self, **kwargs):
        context_data = super(PrivacyPageView, self).get_context_data(**kwargs)
        context_data['nav_bar'] = 'privacy'
        return context_data
