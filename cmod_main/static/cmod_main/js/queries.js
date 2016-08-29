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
                    "label": element['speciesLabel']['value'],
                    "value": element['speciesLabel']['value'],
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
    //console.log(endpoint + queryGenes);
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
                    'label': element['geneLabel']['value'],
                    'locustag': element['locustag']['value'],
                    'id': element['entrezid']['value'],
                    'genomicstart': element['genomicstart']['value'],
                    'genomicend': element['genomicend']['value'],
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
        "SELECT ?protein ?proteinLabel ?goterm  ?reference_stated_inLabel ?reference_retrievedLabel ?determination " +
        "?determinationLabel ?gotermValue ?gotermValueLabel ?goclass ?goclassLabel ?goID WHERE { ?protein wdt:P352",
        "\"" + uniprot + "\".",
        "{?protein p:P680 ?goterm} UNION {?protein p:P681 ?goterm} UNION {?protein p:P682 ?goterm}.  " +
        "?goterm pq:P459 ?determination .  ?goterm prov:wasDerivedFrom/pr:P248 ?reference_stated_in . " +
        "?goterm prov:wasDerivedFrom/pr:P813 ?reference_retrieved . " +
        "{?goterm ps:P680 ?gotermValue} UNION {?goterm ps:P681 ?gotermValue} UNION {?goterm ps:P682 ?gotermValue}.  " +
        "?gotermValue wdt:P279* ?goclass; wdt:P686 ?goID. FILTER ( ?goclass = wd:Q2996394 || ?goclass = wd:Q5058355 || ?goclass = wd:Q14860489) " +
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
        "SELECT distinct ?protein ?interPro_item ?interPro_label ?ipID ?reference_stated_in ?pubDate ?version ?refURL WHERE {" +
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
        "filter (lang(?interPro_label) = \"en\") .}"

    ].join(" ");
    console.log(endpoint + ipQuery);

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


var getAllGoTerms = {
    init: function (input) {
        this.queryAllGoTerms(input)
    },
    queryAllGoTerms: function () {
        return ["SELECT DISTINCT ?goTerm ?goTermLabel ?goID where { ?goTerm wdt:P686 ?goID.",
            "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". ?goTerm rdfs:label ?goTermLabel.}",
            "FILTER(CONTAINS(LCASE(?goTermLabel), \"" + input + "\"))}"].join(" ");
    }


};


//var getSingleGene = function (entrez) {
//    var gene = {};
//    var queryGene = ["SELECT  ?gene ?geneLabel ",
//        "?locustag ?entrezid ?genomicstart ?genomicend",
//        " ?strand ?protein ?proteinLabel ?uniprot ?refseqProtein ",
//        "WHERE {",
//        "?gene wdt:P351",
//        "\"" + entrez + "\";",
//        "wdt:P644 ?genomicstart;",
//        "wdt:P645 ?genomicend;",
//        "wdt:P2393 ?locustag;",
//        "wdt:P2548 ?strand.",
//        "OPTIONAL{?gene wdt:P688 ?protein.",
//        "?protein wdt:P352 ?uniprot;",
//        "wdt:P637 ?refseqProtein.}",
//        "SERVICE wikibase:label {",
//        "bd:serviceParam wikibase:language \"en\" .",
//        "}}"
//    ].join(" ");
//    console.log(queryGene);
//
//    $.ajax({
//        type: "GET",
//        url: endpoint + queryGene,
//        dataType: 'json',
//        success: function (data) {
//            var geneData = data['results']['bindings'];
//            $.each(geneData, function (key, element) {
//                genes = {
//                    'label': element['geneLabel']['value'],
//                    'locustag': element['locustag']['value'],
//                    'id': element['entrezid']['value'],
//                    'genomicstart': element['genomicstart']['value'],
//                    'genomicend': element['genomicend']['value'],
//                    'proteinLabel': element['proteinLabel']['value'],
//                    'uniprot': element['uniprot']['value'],
//                    'refseqProtein': element['refseqProtein']['value'],
//                    'protein': element['protein']['value'],
//                    'gqid': element['gene']['value'],
//                    'pqid': element['protein']['value']
//                };
//
//                geneTags.push(genes);
//
//            });
//
//
//        }
//    });
//    return geneTags;
//
//
//};
//
//
//var getGOTerms2 = function (uniprot) {
//    var goTerms = [];
//    var goQuery = [
//        "SELECT distinct ?pot_go ?goterm_label ?goID ?goclass ?goclass_label WHERE {",
//        "?protein wdt:P352",
//        "\"" + uniprot + "\".",
//        "{?protein wdt:P680 ?pot_go}",
//        "UNION {?protein wdt:P681 ?pot_go}",
//        "UNION {?protein wdt:P682 ?pot_go} .",
//        "?pot_go wdt:P279* ?goclass. ",
//        "?pot_go rdfs:label ?goterm_label.",
//        "?pot_go wdt:P686 ?goID.",
//        "FILTER (LANG(?goterm_label) = \"en\")",
//        "FILTER ( ?goclass = wd:Q2996394 || ?goclass = wd:Q5058355 || ?goclass = wd:Q14860489)",
//        "?goclass rdfs:label ?goclass_label.",
//        "FILTER (LANG(?goclass_label) = \"en\")}"
//
//    ].join(" ");
//
//    $.ajax({
//        type: "GET",
//        url: "https://query.wikidata.org/sparql?format=json&query=" + goQuery,
//        dataType: 'json',
//        success: function (data) {
//
//            $.each(data['results']['bindings'], function (key, element) {
//                goTerms.push(element);
//            });
//        }
//    });
//console.log(goTerms);
//    return goTerms;
//};

//
//var getGenes2 = function (taxid) {
//    var genes = {};
//    var geneTags = [];
//    var queryGenes = ["SELECT  ?gene ?geneLabel ?entrezid ?uniprot" +
//        "WHERE {",
//        "?specieswd wdt:P685",
//        "\"" + taxid + "\".",
//        "?gene wdt:P703 ?specieswd;",
//        "wdt:P351 ?entrezid ;",
//        "SERVICE wikibase:label {",
//        "bd:serviceParam wikibase:language \"en\" .",
//        "}}"
//    ].join(" ");
//
//    $.ajax({
//        type: "GET",
//        url: endpoint + queryGenes,
//        dataType: 'json',
//        success: function (data) {
//            var geneData = data['results']['bindings'];
//            $.each(geneData, function (key, element) {
//                genes = {
//                    'label': element['geneLabel']['value'],
//                    'id': element['entrezid']['value'],
//                    'gene': element['gene']['value']
//                };
//                geneTags.push(genes);
//            });
//        }
//    });
//    return geneTags;
//};
