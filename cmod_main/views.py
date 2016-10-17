from django.http import HttpResponse
from django.template import Context, loader, RequestContext
from django.shortcuts import render, redirect
import json
from .scripts.wikidatabots.ProteinBoxBot_Core import PBB_login, PBB_Core
from .scripts.wikidatabots.genes.microbes import MicrobeBotWDFunctions as WDO
from time import gmtime, strftime, sleep
import pprint
from django.views.decorators.csrf import ensure_csrf_cookie
from mwoauth import ConsumerToken, RequestToken, initiate, complete, identify
import requests
import time
import requests
import json
from requests_oauthlib import OAuth1

# Consruct a "consumer" from the key/secret provided by MediaWiki
from .scripts.utils import oauth_config
from django.http import HttpResponseRedirect


@ensure_csrf_cookie
def index(request):
    # launch landing page
    return render(request, "cmod_main/index.html" ,context={"data":"None"})


@ensure_csrf_cookie
def main_page(request):
    main_page_data = {'verified': "False"}
    if 'oauth_verifier' in request.GET.keys():
        main_page_data['verified'] = "True"
        request.session['oauth_verifier'] = request.GET['oauth_verifier']
        request.session['oauth_token'] = request.GET['oauth_token']
        response_qs = request.META['QUERY_STRING']
        consumer_token = ConsumerToken(request.session['consumer_token']['key'],
                                       request.session['consumer_token']['secret'])
        request_token = RequestToken(request.session['request_token']['key'].encode(),
                                     request.session['request_token']['secret'])
        mw_uri = "https://www.mediawiki.org/w/index.php"
        access_token = complete(mw_uri, consumer_token, request_token, response_qs)
        identity = identify(mw_uri, consumer_token, access_token)
        request.session['username'] = "{username}.".format(**identity)
        request.session['access_token'] = {'key': access_token.key.decode(), 'secret': access_token.secret.decode()}
        request.session['client_key'] = consumer_token.key
        request.session['client_secret'] = consumer_token.secret
        request.session['resource_owner_key'] = access_token.key.decode()
        request.session['resource_owner_secret'] = access_token.secret.decode()

    if 'org' in request.session:
        main_page_data['org_data'] = json.loads(request.session['org'])
        print(request.session.keys())
        return render(request, "cmod_main/main_page.html", main_page_data)
    else:
        main_page_data['org_data'] = {'QID': 'Q21065231', 'RefSeq': 'NC_000915.1', 'Taxid': '85962', 'Name': 'Helicobacter pylori 26695'}
        print(request.session.keys())
        return render(request, "cmod_main/main_page.html", main_page_data)


@ensure_csrf_cookie
def get_orgs(request):
    if request.method == 'POST':
        data = json.dumps(request.POST)
        request.session['org'] = data
        return HttpResponse(request.session['org'], content_type='application/json')
    else:
        return HttpResponse("Hi")


@ensure_csrf_cookie
def wd_go_edit(request):
    if request.method == 'POST':
        edit_status = {}
        # statementData = json.loads(json.dumps(request.POST))
        statementData = json.dumps(request.POST)
        request.session['go'] = statementData
        try:
            auth1 = OAuth1(request.session['client_key'],
                           client_secret=request.session['client_secret'],
                           resource_owner_key=request.session['resource_owner_key'],
                           resource_owner_secret=request.session['resource_owner_secret'])

            goProp = {
                "Q14860489": "P680",
                "Q5058355": "P681",
                "Q2996394": "P682"
            }

            statementDict = json.loads(statementData)

            response_token = requests.get("https://www.wikidata.org/w/api.php",
                                          params={
                                              'action': "query",
                                              'meta': "tokens",
                                              'format': "json"
                                          }, auth=auth1)
            if str(response_token.status_code) == str(200):
                edit_status['code'] = str(response_token.status_code)


            edit_token = response_token.json()['query']['tokens']['csrftoken']

            login = edit_token

            refs = [
                PBB_Core.WDItemID(value='Q26489220', prop_nr='P143', is_reference=True),  # imorted from CMOD
                PBB_Core.WDTime(str(strftime("+%Y-%m-%dT00:00:00Z", gmtime())), prop_nr='P813', is_reference=True)
                # timestamp
            ]

            # Check to see if wikidata has PMID item
            PMID_QID = WDO.WDSparqlQueries(prop='P698', string=statementDict['PMID[pmid]']).wd_prop2qid()
            # reference it if it does
            print(PMID_QID)
            if PMID_QID != 'None':
                edit_status['pmid_ref'] = 'exists'
                ifPub = WDO.WDSparqlQueries(prop='P31', qid=PMID_QID)
                if ifPub == 'Q13442814':
                    refs.append(PBB_Core.WDItemID(value=PMID_QID, prop_nr='P248', is_reference=True))

            # create it if it doesn't
            else:

                pmid_item_statements = [
                    PBB_Core.WDString(prop_nr='P698', value=statementDict['PMID[pmid]']),
                    PBB_Core.WDItemID(prop_nr='P31', value='Q13442814')
                ]
                pmid_wd_item = PBB_Core.WDItemEngine(item_name=statementDict['PMID[title]'], domain=None,
                                                     data=pmid_item_statements)
                pmid_wd_item.write(login, auth1)
                edit_status['pmid_ref'] = 'new'
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
                edit_status["item_search"] = "success"
                print("Found item " + wd_item_protein.get_label())
                pprint.pprint(wd_item_protein.get_wd_json_representation())
                wd_item_protein.write(login, auth1)
                edit_status["write"] = "success"
                print("Wrote item " + wd_item_protein.get_label())
            except Exception as e:
                pprint.pprint(e)

        except Exception as e:
            print(e)
            print("Wikidata edit failed")
            edit_status["item_search"] = "error"
            edit_status["write"] = "error"

        return HttpResponse(json.dumps(edit_status), content_type='application/json')

        # return render(request, "cmod_main/main_page.html",  credentials)


# @ensure_csrf_cookie
# def wd_credentials(request):
#     if request.method == 'POST':
#         creddata = json.dumps(request.POST)
#
#         user_pass = json.loads(creddata)
#         request.session['credentials'] = creddata
#         print("user_pass dj " + str(user_pass))
#         login = PBB_login.WDLogin(user_pass['userName'], user_pass['password'])
#         print("user_pass response wd " + str(login.login_reply))
#         if login.login_reply['login']['result'] == 'Failed':
#             user_pass["login"] = "error"
#         else:
#             user_pass["login"] = "success"
#
#         return HttpResponse(json.dumps(user_pass), content_type='application/json')
#         # return render(request, "cmod_main/main_page.html", )


@ensure_csrf_cookie
def wd_oauth(request):
    if request.method == 'POST':
        oauth = json.dumps(request.POST)
        client_message = json.loads(oauth)
        request.session['oauth'] = client_message['oauth']
        consumer_token = ConsumerToken(oauth_config.consumer_key, oauth_config.consumer_secret)

        request.session['consumer_token'] = {'key': consumer_token.key, 'secret': consumer_token.secret}
        mw_uri = "https://www.mediawiki.org/w/index.php"
        mw_redirect, request_token = initiate(mw_uri, consumer_token)
        request.session['request_token'] = {'key': request_token.key.decode(), 'secret': request_token.secret.decode()}

        return HttpResponse(json.dumps(mw_redirect), content_type='application/json')


@ensure_csrf_cookie
def wd_oauth_deauth(request):
    if request.method == 'POST':
        deauth = json.dumps(request.POST)
        if deauth['deauth'] == "True":
            request.session.flush()


