var endpoint = "https://query.wikidata.org/sparql?format=json&query=";

//get list of organisms from Wikidata with sparql query
var getOrgs = function (callbackOnSuccess) {
    var taxids = {};
    var orgTags = [];
    var queryOrgs = [
        "SELECT ?species ?speciesLabel ?taxid ?RefSeq",
        "WHERE { ?species wdt:P171* wd:Q10876;",
        "wdt:P685 ?taxid; wdt:P2249 ?RefSeq.",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .}}"].join(" ");
    $.ajax({
        type: "GET",
        url: endpoint + queryOrgs,
        dataType: 'json',
        success: function (data) {
            $.each(data['results']['bindings'], function (key, element) {
                var wdid = element['species']['value'].split("/");
                var qid = wdid.slice(-1)[0];
                taxids = {
                    "name": element['speciesLabel']['value'],
                    "value": element['speciesLabel']['value'] + " | " + element['taxid']['value'] + " | " + element['RefSeq']['value'] + " | " + qid,
                    "taxid": element['taxid']['value'],
                    "refseq": element['RefSeq']['value'],
                    'qid': qid
                };
                orgTags.push(taxids);
            });
        }
    });

    callbackOnSuccess(orgTags);
};


var getGenes = function (taxid, callbackOnSuccess) {
    var genes = {};
    var geneTags = [];
    var queryGenes = ["SELECT  ?gene ?specieswd ?specieswdLabel ?taxid ?genomeaccession ?geneLabel ",
        "?locustag ?entrezid ?genomicstart ?genomicend ?strand ?protein ?proteinLabel ?uniprot ?refseqProtein ",
        "WHERE {",
        "?specieswd wdt:P685",
        "\"" + taxid + "\".",
        "?specieswd wdt:P685 ?taxid;",
        "wdt:P2249 ?genomeaccession.",
        "?gene wdt:P703 ?specieswd;",
        "wdt:P351 ?entrezid ;",
        "wdt:P644 ?genomicstart;",
        "wdt:P645 ?genomicend;",
        "wdt:P2393 ?locustag;",
        "wdt:P2548 ?strand.",

        "OPTIONAL{?gene wdt:P688 ?protein.",
        "?protein wdt:P352 ?uniprot;",
        "wdt:P637 ?refseqProtein.}",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .",
        "}}"
    ].join(" ");
    //console.log(queryGenes);
    $.ajax({
        type: "GET",
        url: endpoint + queryGenes,
        dataType: 'json',
        success: function (data) {
            var geneData = data['results']['bindings'];
            $.each(geneData, function (key, element) {
                var gdid = element['gene']['value'].split("/");
                var gqid = gdid.slice(-1)[0];
                genes = {
                    'name': element['geneLabel']['value'],
                    'value': element['geneLabel']['value'] + " | " + element['locustag']['value'] + " | " + gqid + " | " + element['entrezid']['value'],
                    'locustag': element['locustag']['value'],
                    'id': element['entrezid']['value'],
                    'genomicstart': element['genomicstart']['value'],
                    'genomicend': element['genomicend']['value'],
                    'strand': element['strand']['value'],
                    'gqid': gqid
                };

                if (element.hasOwnProperty('protein')) {
                    var pdid = element['protein']['value'].split("/");
                    var pqid = pdid.slice(-1)[0];
                    genes['proteinLabel'] = element['proteinLabel']['value'];
                    genes['uniprot'] = element['uniprot']['value'];
                    genes['refseqProtein'] = element['refseqProtein']['value'];
                    genes['protein'] = pqid;
                }

                geneTags.push(genes);

            });
            callbackOnSuccess(geneTags);
        }
    });


};

var getGOTerms = function (uniprot, callBackonSuccess) {
    var goTerms = {};
    var goQuery = [
        "SELECT ?protein ?proteinLabel ?goterm  ?reference_stated_inLabel ?reference_retrievedLabel ?determination  " +
        "?determinationLabel ?gotermValue ?gotermValueLabel ?goclass ?goclassLabel ?goID ?ecnumber ?pmid WHERE { ?protein wdt:P352",
        "\"" + uniprot + "\".",
        "{?protein p:P680 ?goterm} UNION {?protein p:P681 ?goterm} UNION {?protein p:P682 ?goterm}.  " +
        "?goterm pq:P459 ?determination .  ?goterm prov:wasDerivedFrom/pr:P248 ?reference_stated_in . " +
        "?goterm prov:wasDerivedFrom/pr:P813 ?reference_retrieved . " +
        "OPTIONAL {?goterm prov:wasDerivedFrom/pr:P698 ?pmid .}" +
        "{?goterm ps:P680 ?gotermValue} UNION {?goterm ps:P681 ?gotermValue} UNION {?goterm ps:P682 ?gotermValue}.  " +
        "?gotermValue wdt:P279* ?goclass; wdt:P686 ?goID. FILTER ( ?goclass = wd:Q2996394 || ?goclass = wd:Q5058355 || ?goclass = wd:Q14860489) " +
        "OPTIONAL {?gotermValue wdt:P591 ?ecnumber.}" +
        "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" .}}"

    ].join(" ");
    //console.log(endpoint + goQuery);

    $.ajax({
        type: "GET",
        url: endpoint + goQuery,
        dataType: 'json',
        success: function (data) {
            //console.log(data);
            var mf = [];
            var bp = [];
            var cc = [];

            $.each(data['results']['bindings'], function (key, element) {
                if (element['goclass']['value'] == 'http://www.wikidata.org/entity/Q2996394') {
                    //console.log(element['goclass_label']['value']);
                    bp.push(element);
                }
                if (element['goclass']['value'] == 'http://www.wikidata.org/entity/Q14860489') {
                    //console.log(element);
                    mf.push(element);
                }
                if (element['goclass']['value'] == 'http://www.wikidata.org/entity/Q5058355') {
                    //console.log(element);
                    cc.push(element);
                }


            });
            goTerms['molecularFunction'] = mf;
            goTerms['biologicalProcess'] = bp;
            goTerms['cellularComponent'] = cc;
            callBackonSuccess(goTerms);
        }
    });

};


var getInterPro = function (uniprot, callBackonSuccess) {
    var ipDomains = {};
    var ipQuery = [
        "SELECT distinct ?protein ?interPro_item ?interPro_label ?ipID ?reference_stated_inLabel ?pubDate ?version ?refURL WHERE {" +
        "?protein wdt:P352",
        "\"" + uniprot + "\";",
        "p:P527 ?interPro." +
        "?interPro ps:P527 ?interPro_item;" +
        "prov:wasDerivedFrom/pr:P248 ?reference_stated_in ;" +  //#where stated
        "prov:wasDerivedFrom/pr:P577 ?pubDate ;" + //#when published
        "prov:wasDerivedFrom/pr:P348 ?version ;" + //#software veresion
        "prov:wasDerivedFrom/pr:P854 ?refURL . " + //#reference URL
        "?interPro_item wdt:P2926 ?ipID;" +
        "rdfs:label ?interPro_label. " +
        "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" .}"+
        "filter (lang(?interPro_label) = \"en\") .}"

    ].join(" ");
    //console.log(endpoint + ipQuery);

    $.ajax({
        type: "GET",
        url: endpoint + ipQuery,
        dataType: 'json',
        success: function (data) {
            //console.log(data);
            var ipD = [];
            $.each(data['results']['bindings'], function (key, element) {
                ipD.push(element);

            });
            ipDomains['InterPro'] = ipD;

            //console.log(bp);
            callBackonSuccess(ipDomains);
        }
    });

};




