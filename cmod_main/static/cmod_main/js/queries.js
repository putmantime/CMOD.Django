var endpoint = "https://query.wikidata.org/sparql?format=json&query=";


var getOrgsSimple = [


];
//get list of organisms from Wikidata with sparql query
var getOrgs = function (callbackOnSuccess) {
    var taxids = {};
    var sc = {
                    "name": "Saccharomyces cerevisiae S288c",
                    "value": "Saccharomyces cerevisiae S288c" + " | " + "559292" + " | " + "Q27510868",
                    "taxid": "559292",
                    "refseq": '',
                    'qid': "Q27510868"
                };
    var orgTags = [sc];
    var queryOrgs = [
        "SELECT ?species ?speciesLabel ?taxid ?RefSeq",
        "WHERE { ?species wdt:P171* wd:Q10876;",
        "wdt:P685 ?taxid; wdt:P2249 ?RefSeq.",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .}}"].join(" ");
    //console.log(queryOrgs);
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
        "?locustag ?entrezid ?genomicstart ?genomicend ?strand ?protein ?proteinLabel ?uniprot ?refseqProtein " +
        "?refSeqChromosome",
        "WHERE {",
        "?specieswd wdt:P685",
        "\"" + taxid + "\".",
        "?specieswd wdt:P685 ?taxid.",
        "OPTIONAL {?specieswd wdt:P2249 ?genomeaccession.}",
        "?gene wdt:P703 ?specieswd;",
        "wdt:P351 ?entrezid ;",
        "wdt:P644 ?genomicstart;",
        "wdt:P645 ?genomicend;",
        "wdt:P2393 ?locustag;",
        "wdt:P2548 ?strand;",
        "p:P644 ?chr.",

        "OPTIONAL{?gene wdt:P688 ?protein.",
        "?chr pq:P2249 ?refSeqChromosome.",
        "?protein wdt:P352 ?uniprot;",
        "wdt:P637 ?refseqProtein.}",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .",
        "}}"
    ].join(" ");
    console.log(queryGenes);
    $.ajax({
        type: "GET",
        url: endpoint + queryGenes,
        dataType: 'json',
        success: function (data) {
            var geneData = data['results']['bindings'];
            var gene_count = 0;
            var chr_count = 0;
            $.each(geneData, function (key, element) {
                gene_count += 1;
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

                if (element.hasOwnProperty('refSeqChromosome')){
                    genes['chromosome'] = element['refSeqChromosome']['value']
                } else{
                    genes['chromosome'] = 'None'
                }

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

            //console.log(gene_count);
            //console.log(chr_count);
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
    //console.log(goQuery);

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
        "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" .}" +
        "filter (lang(?interPro_label) = \"en\") .}"

    ].join(" ");
    //console.log(ipQuery);

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

var getEvidenceCodes = function (callBackonSuccess) {
    var codeslist = [];
    var ev_query = endpoint + [
            "select distinct ?evidence_code ?evidence_codeLabel ?alias ?eviURL where {" +
            "?evidence_code wdt:P31 wd:Q23173209. " +
            "?evidence_code skos:altLabel ?alias." +
            "?evidence_code wdt:P856 ?eviURL." +
            "filter (lang(?alias) = \"en\") " +
            "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" .}",
            "}"
        ].join(" ");
    //console.log(ev_query);

    $.ajax({
        type: "GET",
        url: ev_query,
        dataType: 'json',
        success: function (data) {
            //console.log(data);
            $.each(data['results']['bindings'], function (key, element) {
                var evCodes = {
                    'code': element['evidence_codeLabel']['value'],
                    'qid': element['evidence_code']['value'],
                    'alias': element['alias']['value'],
                    'docs': element['eviURL']['value']
                };
                codeslist.push(evCodes);
            });
            callBackonSuccess(codeslist);
        }
    });

};


var getOperonData = function (entrez, callBackonSuccess) {
    var operonGenes = {};
    var opQuery = [
        "SELECT ?gene ?locusTag ?entrez ?operon ?operonLabel ?genStart",
        "?genEnd ?strand ?strandLabel ?op_genes ?op_genesLabel",
        "WHERE {",
        "?gene wdt:P351 '" + entrez + "';",
        "wdt:P361 ?operon.",
        "?operon wdt:P527 ?op_genes.",
        "?op_genes wdt:P2393 ?locusTag;",
        "wdt:P351 ?entrez;",
        "wdt:P644 ?genStart;",
        "wdt:P645 ?genEnd;",
        "wdt:P2548 ?strand.",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .",
        "}}"
    ].join(" ");
    //console.log(opQuery);

    $.ajax({
        type: "GET",
        url: endpoint + opQuery,
        dataType: 'json',
        success: function (data) {
            //console.log(data);
            var opD = [];
            $.each(data['results']['bindings'], function (key, element) {
                opD.push(element);

            });
            operonGenes['Operon'] = opD;

            //console.log(bp);
            callBackonSuccess(operonGenes);
        }
    });

};

var getOperon = function (entrez, callBackonSuccess) {
    var operon = {};
    var operonQuery = [
        "SELECT ?operon ?operonLabel",
        "WHERE {",
        "?gene wdt:P351 '" + entrez + "';",
        "wdt:P361 ?operon.",
        "SERVICE wikibase:label {",
        "bd:serviceParam wikibase:language \"en\" .",
        "}}"
    ].join(" ");
    //console.log(operonQuery);

    $.ajax({
        type: "GET",
        url: endpoint + operonQuery,
        dataType: 'json',
        success: function (data) {
            //console.log(data);
            var opD = [];
            $.each(data['results']['bindings'], function (key, element) {
                opD.push(element);
            });
            operon['Operon'] = opD;

            //console.log(bp);
            callBackonSuccess(operon);
        }
    });

};