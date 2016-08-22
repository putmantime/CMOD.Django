from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.shortcuts import render
import json
from .scripts.wikidatabots.ProteinBoxBot_Core import PBB_login, PBB_Core
from time import gmtime, strftime
import pprint

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
        # statementData = json.loads(json.dumps(request.POST))
        statementData = json.dumps(request.POST)
        request.session['go'] = statementData
        login = PBB_login.WDLogin()
        statementDict = json.loads(statementData)
        goProp = {
            "Molecular Function": "P680",
            "Cellular Component": "P681",
            "Biological Process": "P682"
        }
        refs = [PBB_Core.WDItemID(value='Q591041', prop_nr='P248', is_reference=True),  # stated in
                PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language
                PBB_Core.WDString(value=statementDict['PMID'], prop_nr='P698', is_reference=True),  # PMID
                PBB_Core.WDItemID(value='Q26489220', prop_nr='P143', is_reference=True),  # imorted from CMOD
                PBB_Core.WDTime(str(strftime("+%Y-%m-%dT00:00:00Z", gmtime())), prop_nr='P813', is_reference=True)
                # timestamp
                ]

        for ref in refs:
            ref.overwrite_references = False

            evidence = PBB_Core.WDItemID(value=statementDict['evidenceCode'], prop_nr='P459', is_qualifier=True)
            goStatement = PBB_Core.WDItemID(value=statementDict['goTerm'], prop_nr=goProp[statementDict['goClass']],
                                            references=[refs], qualifiers=[evidence])

            try:
                # find the appropriate item in wd or make a new one
                wd_item_protein = PBB_Core.WDItemEngine(wd_item_id=statementDict['subject'], domain='proteins',
                                                        data=[goStatement],
                                                        use_sparql=True)
                print("Found item " + wd_item_protein.get_label())
                wd_item_protein.write(login)
                print("Wrote item " + wd_item_protein.get_label())
            except Exception as e:
                pprint.pprint(e)



        return HttpResponse(request.session['go'], content_type='application/json')

    else:
        return HttpResponse("Hi")


def wd_credentials(request):
    if request.method == 'POST':
        creddata = json.dumps(request.POST)
        request.session['credentials'] = creddata
        print(creddata)
        print(request.session['credentials'])
        return HttpResponse(request.session['credentials'], content_type='application/json')
