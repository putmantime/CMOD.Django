from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.shortcuts import render
import json
from .scripts.wikidatabots.ProteinBoxBot_Core import PBB_login, PBB_Core
from .scripts.wikidatabots.genes.microbes import MicrobeBotWDFunctions as WDO
from time import gmtime, strftime, sleep
import pprint
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def index(request):
    # launch landing page
    template = loader.get_template("cmod_main/index.html")
    return HttpResponse(template.render())

@ensure_csrf_cookie
def main_page(request):
    org_data = json.loads(request.session['org'])
    # template = loader.get_template("cmod_main/main_page.html")
    return render(request, "cmod_main/main_page.html", org_data)

@ensure_csrf_cookie
def get_orgs(request):
    if request.method == 'POST':
        data = json.dumps(request.POST)
        print(request.META)
        request.session['org'] = data
        return HttpResponse(request.session['org'], content_type='application/json')
    else:
        return HttpResponse("Hi")

@ensure_csrf_cookie
def wd_go_edit(request):
    if request.method == 'POST':

        # statementData = json.loads(json.dumps(request.POST))
        statementData = json.dumps(request.POST)
        request.session['go'] = statementData
        credentials = json.loads(request.session['credentials'])

        print("wd_go_edit " + str(credentials))

        try:
            print(credentials['userName'], credentials['password'])
            login = PBB_login.WDLogin(credentials['userName'], credentials['password'])

            credentials["login"] = "success"
            statementDict = json.loads(statementData)
            print(statementDict)

            goProp = {
                "Q14860489": "P680",
                "Q5058355": "P681",
                "Q2996394": "P682"
            }

            refs = [
                    PBB_Core.WDItemID(value='Q26489220', prop_nr='P143', is_reference=True),  # imorted from CMOD
                    PBB_Core.WDTime(str(strftime("+%Y-%m-%dT00:00:00Z", gmtime())), prop_nr='P813', is_reference=True) # timestamp
                    ]

            # Check to see if wikidata has PMID item
            PMID_QID = WDO.WDSparqlQueries(prop='P698', string=statementDict['PMID[pmid]']).wd_prop2qid()
            #reference it if it does
            print("hello")
            print(PMID_QID)
            if PMID_QID != 'None':
                ifPub = WDO.WDSparqlQueries(prop='P31', qid=PMID_QID)
                if ifPub == 'Q13442814':
                    refs.append(PBB_Core.WDItemID(value=PMID_QID, prop_nr='P248', is_reference=True))

            #create it if it doesn't
            else:

                pmid_item_statements = [
                    PBB_Core.WDString(prop_nr='P698', value=statementDict['PMID[pmid]']),
                    PBB_Core.WDItemID(prop_nr='P31', value='Q13442814')
                ]
                pmid_wd_item = PBB_Core.WDItemEngine(item_name=statementDict['PMID[title]'], domain=None, data=pmid_item_statements)
                pmid_wd_item.write(login)
                # now reference the new item that was just created
                refs.append(PBB_Core.WDItemID(value=pmid_wd_item.wd_item_id, prop_nr='P248', is_reference=True))

            for ref in refs:
                ref.overwrite_references = False

            evidence = PBB_Core.WDItemID(value=statementDict['evidenceCode'], prop_nr='P459', is_qualifier=True)
            goStatement = PBB_Core.WDItemID(value=statementDict['goTerm'], prop_nr=goProp[statementDict['goClass']],
                                            references=[refs], qualifiers=[evidence])



            try:
                # find the appropriate item in wd or make a new one
                wd_item_protein = PBB_Core.WDItemEngine(wd_item_id=statementDict['subject'], domain='proteins',
                                                        data=[goStatement], use_sparql=True,
                                                        append_value=[goProp[statementDict['goClass']]])
                print("found the item")
                credentials["item_search"] = "success"
                print("Found item " + wd_item_protein.get_label())
                pprint.pprint(wd_item_protein.get_wd_json_representation())
                wd_item_protein.write(login)
                credentials["write"] = "success"
                print("Wrote item " + wd_item_protein.get_label())
            except Exception as e:
                pprint.pprint(e)

        except Exception as e:
            print(e)
            print("Wikidata edit failed")
            credentials["login"] = "error"
            credentials["item_search"] = "error"
            credentials["write"] = "error"


        return HttpResponse(json.dumps(credentials), content_type='application/json')

        # return render(request, "cmod_main/main_page.html",  credentials)

@ensure_csrf_cookie
def wd_credentials(request):
    if request.method == 'POST':
        creddata = json.dumps(request.POST)

        user_pass = json.loads(creddata)
        request.session['credentials'] = creddata
        print("user_pass dj " + str(user_pass))
        login = PBB_login.WDLogin(user_pass['userName'], user_pass['password'])
        print("user_pass response wd " + str(login.login_reply))
        if login.login_reply['login']['result'] == 'Failed':
            user_pass["login"] = "error"
        else:
            user_pass["login"] = "success"

        return HttpResponse(json.dumps(user_pass), content_type='application/json')
        # return render(request, "cmod_main/main_page.html", )
