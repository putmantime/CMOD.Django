from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.shortcuts import render
import json


def index(request):
    template = loader.get_template("cmod_main/index.html")
    return HttpResponse(template.render())


def main_page(request):
    org_data = json.loads(request.session['org'])
    # template = loader.get_template("cmod_main/main_page.html")
    return render(request, "cmod_main/main_page.html", org_data)
    # return HttpResponse(template.render())


def get_orgs(request):
    if request.method == 'POST':
        data = json.dumps(request.POST)
        request.session['org'] = data
        return HttpResponse(request.session['org'], content_type='application/json')
    else:
        return HttpResponse("Hi")


def wd_go_edit(request):
    if request.method == 'POST':
        data = json.dumps(request.POST)
        request.session['go'] = data
        print("django side:" + data)
        return HttpResponse(request.session['go'], content_type='application/json')
    else:
        return HttpResponse("Hi")

