$(document).ready(function () {
//////////////////////////////////////////Begin Global variables////////////////////////////////////////////////////////
    //organism data determines current state
    var currentTaxa = {
        "Name": OrgName,
        "Taxid": OrgTID,
        "QID": OrgQID,
        "RefSeq": OrgRefSeq
    };
    var verified = verification;


///////////////////////////////////////////End Global Variables/////////////////////////////////////////////////////////
///////////////////////////////////////////Begin form modules///////////////////////////////////////////////////////////
//////organism selection form module//////
    var orgForm = {
        // organism form for selecting organism based on label and return core identifiers to populate currentTaxa
        init: function () {
            this.cacheDOM();
            this.acsource(this.$input);
        },
        cacheDOM: function () {
            // cache the relevant DOM elements once
            this.$of = $("#orgFormModule");
            this.$input = this.$of.find('input');
        },
        // populate organism form with list of bacteria to choose from
        acsource: function (orginput) {
            getOrgs(function (orgTags) {
                orginput.autocomplete({
                    minLength: 0,
                    source: orgTags, //sparql query callback in queries.js
                    autoFocus: true,
                    select: function (event, ui) {
                        $('form').each(function () {
                            this.reset()
                        });
                        orginput.val("");

                        currentTaxa = {
                            'Name': ui.item.name,
                            'Taxid': ui.item.taxid,
                            'QID': ui.item.qid,
                            'RefSeq': ui.item.refseq
                        };


                        //initiate gene form with organism data
                        geneForm.init(currentTaxa.Taxid);
                        //render organism data
                        orgData.init(currentTaxa);
                        annotations.init(currentTaxa.Taxid);

                        return false;
                    }
                })
                    //custom template for org search box
                    .autocomplete("instance")._renderItem = function (ul, item) {
                    return $("<li>")
                        .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><i><u><strong>" +
                        item.name + "</strong></u></i><br>Taxid: " + item.taxid + "<br>Wikidata: " +
                        item.qid + "</div>")
                        .appendTo(ul);
                };
            });

        }
    };
    orgForm.init();

//////gene selection form module//////
    var geneForm = {
        currentGene: [],
        currentProtein: [],
        init: function (taxid) {
            this.cacheDOM();
            this.geneDataAC(taxid);

        },
        cacheDOM: function () {
            this.$gf = $("#geneFormModule");
            this.$input = this.$gf.find('input');

        },
        geneDataAC: function (taxid) {
            var geneinput = this.$input;
            getGenes(taxid, function (geneTags) {
                geneinput.autocomplete({
                    minLength: 2,
                    source: geneTags,
                    autoFocus: true,
                    select: function (event, ui) {
                        $('form').each(function () {
                            this.reset()
                        });
                        $("#geneData, #protData, .main-go-data .main-operon-genes-data .main-operon-data ").html("");
                        geneinput.val("");

                        this.currentGene = [
                            ui.item.name,
                            ui.item.id,
                            ui.item.gqid,
                            ui.item.locustag,
                            ui.item.genomicstart,
                            ui.item.genomicend,
                            ui.item.strand,
                            ui.item.chromosome

                        ];
                        this.currentProtein = [
                            ui.item.proteinLabel,
                            ui.item.uniprot,
                            ui.item.protein,
                            ui.item.refseqProtein

                        ];

                        //get GO Terms for this gene/protein
                        //goData.init(this.currentProtein[1]);
                        goData.init(this.currentProtein[1]);
                        operonData.init(this.currentGene[1]);
                        interProData.init(this.currentProtein[1]);
                        genPosData.init(this.currentGene);
                        //Render the data into the gene and protein boxes
                        geneData.init(this.currentGene);
                        proteinData.init(this.currentProtein);
                        //initialize the goform
                        //console.log(this.currentProtein[2]);
                        goFormAll.init(this.currentProtein[2]);
                        operonFormAll.init(this.currentGene[2]);
                        //focus jbrowse on selected gene
                        var gstart = this.currentGene[4] - 5000;
                        var gend = this.currentGene[5] - (-5000);
                        jbrowse.init(currentTaxa.Taxid, this.currentGene[7], ":" + gstart + ".." + gend, currentTaxa.Name);
                        return false;
                    }
                })
                    //custom template for gene search box
                    .autocomplete("instance")._renderItem = function (ul, item) {
                    return $("<li>")
                        .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.name +
                        "</u></strong><br>Entrez ID:" + item.id + "<br>Wikidata: " + item.gqid + "</div>")
                        .appendTo(ul);
                };
                //initialize gene and protein boxes on page load with random gene/protein
                //console.log(geneTags[0]);
                var first_gene = [
                    geneTags[0].name,
                    geneTags[0].id,
                    geneTags[0].gqid,
                    geneTags[0].locustag,
                    geneTags[0].genomicstart,
                    geneTags[0].genomicend,
                    geneTags[0].strand,
                    geneTags[0].chromosome

                ];
                var first_protein = [
                    geneTags[0].proteinLabel,
                    geneTags[0].uniprot,
                    geneTags[0].protein,
                    geneTags[0].refseqProtein

                ];
                //initialize all modules on organism load
                geneData.init(first_gene);
                operonData.init(first_gene[1]);
                proteinData.init(first_protein);
                interProData.init(first_protein[1]);
                genPosData.init(first_gene);
                //goData.init(first_protein[1]);
                goData.init(first_protein[1]);
                goFormAll.init(first_protein[2]);
                operonFormAll.init(first_gene[2]);
                var gstart = first_gene[4] - 20000;
                var gend = first_gene[5] - (-20000);
                //console.log(gend);
                jbrowse.init(currentTaxa.Taxid, first_gene[7], ":" + gstart + ".." + gend, currentTaxa.Name);
            })
        }

    };

//////////////////////goformdev//////////////////////////
    //////Go form module//////
    var goFormAll = {
        goFormData: {},
        endpoint: "https://query.wikidata.org/sparql?format=json&query=",
        init: function (subjectQID) {
            this.goFormData["subject"] = subjectQID;
            this.cacheDOM();
            this.goTermsAC();
            this.pmidForm();
            this.editWD();
            this.evidenceCodes();
            this.resetForm();


        },
        cacheDOM: function () {
            this.$goTermForm = $('#main-go-form');
            this.$goForm = this.$goTermForm.find('#goTermForm');
            this.$goEviForm = this.$goTermForm.find('#eviCodeForm');
            this.$pmidForm = this.$goTermForm.find('#pmidForm');
            this.$radiobutton = this.$goTermForm.find('#go-radio');
            this.$editWDButton = this.$goTermForm.find('#editWDButton');
        },
        resetForm: function () {
            $('.modal').on('hidden.bs.modal', function () {
                $(this).find('form')[0].reset();

            });

        },

        goTermsAC: function () {
            var goClassButton = {
                mfbutton: ['Q14860489', 'Molecular Function'],
                bpbutton: ['Q2996394', 'Biological Process'],
                ccbutton: ['Q5058355', 'Cellular Component']

            };
            var goClassButtonElem;
            $('.main-goButton').on('click', function (e) {
                if (verified === 'False') {
                    alert("To make an annotation, you must first authorize WikiGenome.org to edit Wikidata. " +
                        "Please click the 'Authorize to Edit Wikidata' button to begin the process");
                    e.stopPropagation();
                }
                goClassButtonElem = goClassButton[$(this).attr('id')];
                goFormAll.goFormData["goClass"] = goClassButtonElem[0];
                $('#myGOModalLabel').html("<span>Add a " + goClassButtonElem[1] + " to this protein</span>");

            });

            this.$goForm.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: goFormAll.endpoint +
                        ["SELECT DISTINCT ?goterm ?goID ?goterm_label",
                            "WHERE {",
                            "?goterm wdt:P279* wd:" +
                            goClassButtonElem[0] +
                            "; rdfs:label ?goterm_label;",
                            "wdt:P686 ?goID.",
                            "FILTER(lang(?goterm_label) = \"en\")",
                            "FILTER(CONTAINS(LCASE(?goterm_label), \"" +
                            request.term.toLowerCase() +
                            "\" ))}"].join(" "),
                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['results']['bindings'], function (key, element) {
                                var wdid = element['goterm']['value'].split("/");
                                var orgqid = wdid.slice(-1)[0];
                                data_hash = {
                                    'label': element['goterm_label']['value'],
                                    'value': element['goterm_label']['value'],
                                    'id': element['goID']['value'],
                                    'qid': orgqid
                                };
                                data_array.push(data_hash);
                            });
                            response(data_array);
                        }
                    });
                },
                select: function (event, ui) {
                    goFormAll.goFormData["goTerm"] = ui.item.qid;
                    //console.log(goFormAll.goFormData);


                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>Gene Ontology ID: " + item.id + "<br>Wikidata: " + item.qid + "</div>")
                    .appendTo(ul);
            };


        },

        evidenceCodes: function () {

            getEvidenceCodes(function (evCodes) {
                var optlist = $('#optlist');
                $.each(evCodes, function (key, element) {

                    //this refers to the current item being iterated over
                    var $indlist = $('<li></li>');
                    var $inda = $("<div style='border-bottom:solid black 1px; height:50px; padding:10px' class='hov' id='" + element.qid + "'style=\"border-bottom: solid black 1px\">" + element.alias + "<a  id='evdocbutton' target='_blank' href='" + element.docs + "' class='btn btn-default' role='button'>" + '?' + "</a></div>");

                    $indlist.html($inda);
                    optlist.append($indlist);
                });
                var $focused = $('#optlist li div');
                $focused.on('hover', function () {
                    this.addClass();
                });
                $focused.off("click").click(function (e) {
                    var qidURL = $(this).attr('id');
                    var wdid = qidURL.split("/");
                    goFormAll.goFormData["evidenceCode"] = wdid.slice(-1)[0];
                    //console.log(goFormAll.goFormData);
                    $('#evCodeChoice').html("<span>" + $(this).text().slice(0, -1) + "</span>");

                });


            });
        },
        pmidForm: function () {
            //form for looking a publication to provide as a reference using eutils
            this.$pmidForm.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + request.term,
                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['result'], function (key, element) {
                                data_hash = {
                                    'label': element['title'],
                                    'value': element['uid'],
                                    'id': element['uid'],
                                    'first_author': element['sortfirstauthor'],
                                    'journal': element['fulljournalname'],
                                    'year': element['pubdate']

                                };
                                data_array.push(data_hash);
                            });
                            response([data_array[0]]);

                        }
                    });
                },
                select: function (event, ui) {
                    goFormAll.goFormData["PMID"] = {
                        'pmid': ui.item.id,
                        'title': ui.item.label
                    };

                    //console.log(goFormAll.goFormData);
                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>PMID" + item.id + "<br>" + item.first_author + "<i> et al. </i>" + item.year +
                    "</u></strong><br>Publication:" + item.journal + "</div>")
                    .appendTo(ul);
            };

        },
        editWD: function () {

            this.$editWDButton.off("click").click(function (e) {
                e.preventDefault();
                goFormAll.sendToServer(goFormAll.goFormData, '/wd_go_edit');
                $('form').each(function () {
                    this.reset()
                });
            });


        },
        sendToServer: function (data, urlsuf) {
            var csrftoken = getCookie('csrftoken');
            $.ajax({
                type: "POST",
                url: window.location.pathname + urlsuf,
                data: data,
                dataType: 'json',
                headers: {'X-CSRFToken': csrftoken},
                success: function (data) {
                    console.log("go data success");
                    //console.log(data);
                    //alert("Successful interaction with the server");
                    if (data['write'] === "success") {
                        alert("Wikidata item succesfully edited!\nIt may take a few minutes for it to show up here.");
                    }
                    else {
                        alert("Could not edit Wikidata at this time");
                    }

                },
                error: function (data) {
                    console.log("go data error");
                    //console.log(data);
                    //alert("Something went wrong interacting with the server");
                }
            });
        }
    };


//////////////////////goformdev//////////////////////////
/////////////////////operon form////////////////////////
    var operonFormAll = {
        operonFormData: {
            operonQID: 'None',
            otherGenes: [],
            locusTags: [],
            authorized: verified,
            organism: currentTaxa.Name
        },
        endpoint: "https://query.wikidata.org/sparql?format=json&query=",
        init: function (subjectQID) {
            this.operonFormData["subject"] = subjectQID;
            this.cacheDOM();
            this.operonAC();
            this.geneOperonAC();
            this.pmidForm();
            this.editWD();
            this.resetForm();


        },
        cacheDOM: function () {
            this.$operonFormGroup = $('#main-operon-form');
            this.$operon_input = this.$operonFormGroup.find('#operonForm');
            this.$gene_input = this.$operonFormGroup.find('#operonGenesForm');
            this.$pmid_input = this.$operonFormGroup.find('#op_pmidForm');
            this.$editwdButton = this.$operonFormGroup.find('#opeditWDButton');
            this.$op_modal_button = $("#opbutton");

        },
        resetForm: function () {
            $('.modal').on('hidden.bs.modal', function () {
                $('form').each(function () {
                    this.reset()
                });
                $('#opNameStaging').html('');
                $('#opGeneStaging').html('');
                $('#opPMIDStaging').html('');
            });
            this.$op_modal_button.off("click").click(function (e) {
                e.preventDefault();
                if (verified === 'False') {
                    alert("To make an annotation, you must first authorize WikiGenome.org to edit Wikidata. " +
                        "Please click the 'Authorize to Edit Wikidata' button to begin the process");
                    e.stopPropagation();
                }
                operonFormAll.operonFormData["PMID"] = {};
                operonFormAll.operonFormData["otherGenes"] = [];
                operonFormAll.operonFormData["locusTags"] = [];
            });

        },
        geneOperonAC: function () {
            this.$gene_input.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 2,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: operonFormAll.endpoint +
                        ["SELECT DISTINCT ?gene ?gene_label ?entrez ?locus_tag " +
                        "WHERE { " +
                        "?gene wdt:P279 wd:Q7187; " +
                        "wdt:P703 wd:" + currentTaxa.QID + ";",
                            "wdt:P351 ?entrez;" +
                            "wdt:P2393 ?locus_tag;" +
                            "rdfs:label ?gene_label. " +
                            "FILTER(lang(?gene_label) = \"en\") " +
                            "FILTER(CONTAINS(LCASE(?gene_label), \"" +
                            request.term.toLowerCase() +
                            "\" ))}"
                        ].join(" "),
                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['results']['bindings'], function (key, element) {
                                var wdid = element['gene']['value'].split("/");
                                var geneqid = wdid.slice(-1)[0];
                                data_hash = {
                                    'label': element['gene_label']['value'],
                                    'value': element['gene_label']['value'],
                                    'id': element['entrez']['value'],
                                    'lt': element['locus_tag']['value'],
                                    'qid': geneqid
                                };
                                data_array.push(data_hash);
                            });
                            response(data_array);
                        }
                    });
                },
                select: function (event, ui) {
                    operonFormAll.operonFormData["otherGenes"].push(ui.item.qid);
                    operonFormAll.operonFormData["locusTags"].push(ui.item.lt);
                    //console.log(operonFormAll.operonFormData);
                    $('#opGeneStaging').html("<span><h5>has genes: </h5>" + operonFormAll.operonFormData['locusTags'].join(", "));
                    $('#operonGenesForm').val('');
                    return false;
                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>Wikidata: " + item.qid + "<br>Entrez ID: " + item.id + "<br>NCBI Locus Tag: " + item.lt + "</div>")
                    .appendTo(ul);
            };


        },
        operonAC: function () {
            this.$operon_input.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: operonFormAll.endpoint +
                        ["SELECT DISTINCT ?operon ?operon_label " +
                        "WHERE { " +
                        "?operon wdt:P279 wd:Q139677; " +
                        "wdt:P703 wd:" + currentTaxa.QID,
                            "; rdfs:label ?operon_label. " +
                            "FILTER(lang(?operon_label) = \"en\") " +
                            "FILTER(CONTAINS(LCASE(?operon_label), \"" +
                            request.term.toLowerCase() + "\")) }"
                        ].join(" "),

                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            //console.log(data['results']['bindings']);
                            if (data['results']['bindings'].length === 0) {
                                data_hash = {
                                    'label': "No operon found --  Enter the full name here and Click 'Submit' to set the operon's name",
                                    'value': 'None',
                                    'id': 'None',
                                    'qid': 'None'
                                };
                                operonFormAll.submitNewName();
                                data_array.push(data_hash);
                            }
                            else {
                                $.each(data['results']['bindings'], function (key, element) {
                                    var wdid = element['operon']['value'].split("/");
                                    var opqid = wdid.slice(-1)[0];
                                    data_hash = {
                                        'label': element['operon_label']['value'],
                                        'value': element['operon_label']['value'],
                                        'id': opqid,
                                        'qid': opqid
                                    };
                                    data_array.push(data_hash);
                                });
                            }
                            response(data_array);
                        }
                    });
                },
                select: function (event, ui) {
                    operonFormAll.operonFormData["operonQID"] = ui.item.qid;
                    if (ui.item.value != 'None') {
                        operonFormAll.operonFormData["operonName"] = ui.item.label;
                        $('#opNameStaging').html("<span><h5><strong>" + operonFormAll.operonFormData["operonName"] + "</strong></h5>");
                    }
                    else {
                        operonFormAll.operonFormData["operonName"] = 'None';
                    }
                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>Wikidata: " + item.qid + "</div>")
                    .appendTo(ul);
            };


        },
        submitNewName: function () {
            $('#opnameButton').off("click").click(function (e) {
                e.preventDefault();
                operonFormAll.operonFormData['operonName'] = operonFormAll.$operon_input.val();
                $('#opNameStaging').html("<span><h5><strong>" + operonFormAll.operonFormData["operonName"] + "</strong></h5>");
            });
        },
        pmidForm: function () {
            //form for looking a publication to provide as a reference using eutils
            this.$pmid_input.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + request.term,
                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['result'], function (key, element) {
                                data_hash = {
                                    'label': element['title'],
                                    'value': element['uid'],
                                    'id': element['uid'],
                                    'first_author': element['sortfirstauthor'],
                                    'journal': element['fulljournalname'],
                                    'year': element['pubdate']

                                };
                                data_array.push(data_hash);
                            });
                            response([data_array[0]]);

                        }
                    });
                },
                select: function (event, ui) {
                    operonFormAll.operonFormData["PMID"] = {
                        'pmid': ui.item.id,
                        'title': ui.item.label,
                        'author': ui.item.first_author,
                        'year': ui.item.year
                    };
                    $('#opPMIDStaging').html("<span><h5>stated in:</h5>" + operonFormAll.operonFormData['PMID']['author'] + "<i> et. al </i>" + operonFormAll.operonFormData['PMID']['year']);


                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>PMID" + item.id + "<br>" + item.first_author + "<i> et al. </i>" + item.year +
                    "</u></strong><br>Publication:" + item.journal + "</div>")
                    .appendTo(ul);
            };

        },
        editWD: function () {

            this.$editwdButton.off("click").click(function (e) {
                e.preventDefault();
                console.log(operonFormAll.operonFormData);

                operonFormAll.sendToServer(operonFormAll.operonFormData, '/wd_operon_edit');
                $('form').each(function () {
                    this.reset()
                });

            });


        },
        sendToServer: function (data, urlsuf) {
            console.log("send to server");
            console.log(data);
            var csrftoken = getCookie('csrftoken');
            console.log(csrftoken);
            $.ajax({
                type: "POST",
                url: window.location.pathname + urlsuf,
                data: data,
                dataType: 'json',
                headers: {'X-CSRFToken': csrftoken},
                success: function (data) {
                    console.log("operon data success");
                    console.log(data);
                    if (data['write'] === "success") {
                        alert("Wikidata item succesfully edited!\nIt may take a few minutes for it to show up here.");
                    }
                    else {
                        console.log(csrftoken);
                        alert("Could not edit Wikidata at this time");
                    }
                },
                error: function (data) {
                    console.log("operon data error");
                    console.log(data);
                    alert("Something went wrong interacting with the server");
                }
            });
        }

    };
    ////////////////////////////////////////////////////////////////////

//////////////////////////////////////////End form modules//////////////////////////////////////////////////////////////


////////////////////////////////////Begin data rendering modules////////////////////////////////////////////////////////
//////render the organism data in the Organism box//////

    var orgData = {
        init: function (taxData) {
            this.cacheDOM();

            this.render(taxData);

        },
        cacheDOM: function () {
            this.$od = $("#orgDataModule");
            this.$ul = this.$od.find('ul');
            this.$orgD = this.$od.find('#orgData');
            this.$tid = this.$od.find('#taxid');
            this.$qid = this.$od.find('#QID');
            this.$rsid = this.$od.find('#RefSeq');
            this.$name = this.$od.find('#main-organism-name');
            //this.templateORG = this.$od.find('#org-template').html();
            //console.log($('#org-template').html());

        },
        render: function (taxData) {

            var data = {
                'organism': taxData,
                'thing': 'thing'
            };
            this.$name.html("<span><h4><i><strong>" + data['organism']['Name'] + "</strong></i></h4>");
            this.$tid.html("<span><h6>NCBI Taxonomy ID: " +
                "</h6><a href='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=" +
                data['organism']['Taxid'] + "'>" + data['organism']['Taxid'] + " </a></span>");
            //console.log(this.$tid.html());
            this.$qid.html("<span><h6>Wikidata Item ID:</h6><a href='https://www.wikidata.org/wiki/" + data['organism']['QID'] + "'>" + data['organism']['QID'] + "</span>");
            //this.$rsid.html("<span><h5>NCBI RefSeq ID</h5>" + data['organism']['RefSeq'] + "</span>");

        }
    };

//////render the gene data in Gene box//////

    var geneData = {
        init: function (gene) {
            this.cacheDOM();
            this.$geneD.html('');
            this.render(gene);


        },
        cacheDOM: function () {
            this.$gd = $("#geneDataModule");
            this.$ul = this.$gd.find('ul');
            this.$geneD = this.$gd.find('#geneData');
            this.$annotations = this.$gd.find('#geneannotationdata');
            this.$gene_template = this.$gd.find('#gene_data_template');
            this.template = this.$gd.find('#gene-template').html();

        },
        render: function (gene) {
            var data = {
                'gene': gene,
                'name': gene[0],
                'entrez': gene[1],
                'qid': gene[2],
                'locus_tag': gene[3],
                'gen_start': gene[4],
                'gen_end': gene[5]
            };
            if (gene[6] === 'http://www.wikidata.org/entity/Q22809711') {
                data['strand'] = 'Reverse';
            }
            else {
                data['strand'] = 'Forward';
            }

            //console.log(data);
            var template = _.template(
                "<div class='main-data'> <h5>Gene Name: </h5><a target='_blank' href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= entrez %>'><%= name %></a> </div>" +
                "<div class='main-data'> <h5>Entrez ID: </h5> <a target='_blank' href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= entrez %>'><%= entrez %></a></div>" +
                "<div class='main-data'> <h5>Wikidata ID: </h5> <a target='_blank' href='https://www.wikidata.org/wiki/<%= qid %>'><%= qid %></a></div>" +
                "<div class='main-data'> <h5>NCBI Locus Tag: </h5> <a target='_blank' href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= locus_tag %>'><%= locus_tag %></a></div>"
            );
            this.$geneD.html(template(data));
            geneRefModal_obj.init(this.$annotations, '-------', '-------');
        }
    };

    var genPosData = {
        init: function (gene) {
            this.cacheDOM();
            this.render(gene);
            geneRefModal_obj.init(gene);
        },
        cacheDOM: function () {
            this.$gp = $('#genPosData');
        },
        render: function (gene_data) {
            var data = {
                "accession": gene_data[7],
                "genStart": gene_data[4],
                "genEnd": gene_data[5]

            };
            if (gene_data[6] === 'http://www.wikidata.org/entity/Q22809711') {
                data['strand'] = 'Reverse';
            }
            else {
                data['strand'] = 'Forward';
            }


            var template = _.template(
                "<div class='row main-dataul'>" +
                "<div class='col-xs-2'><h5><%= accession %></h5></div>" +
                "<div class='col-xs-2'><h5><%= genStart %></h5></div>" +
                "<div class='col-xs-2'><h5><%= genEnd %></h5></div>" +
                "<div class='col-xs-2'><h5><%= strand %></h5></div>" +
                "<div class='col-xs-2'></div>" +
                "<div id='main-ref-button'class='col-xs-2'>" +
                "<button type='button' id='genPosRef' class='main-button-ref btn btn-default div-ref-but' ></button>" +
                "</div></div>"
            );

            this.$gp.html(template(data));

        }
    };

//////render the protein dat in the Protein box///////

    var proteinData = {
        init: function (protein) {
            this.cacheDOM();
            this.$protD.html('');
            this.render(protein);

        },
        cacheDOM: function () {
            this.$pd = $("#protDataBox");
            this.$ul = this.$pd.find('ul');
            this.$protD = this.$pd.find('#protData');
            this.template = this.$pd.find('#protein-template').html();

        },
        render: function (protein) {
            //console.log(protein);

            var data = {
                'protein': protein,
                'name': protein[0],
                'uniprot': protein[1],
                'qid': protein[2],
                'refseq': protein[3]
            };
            //console.log(protein); //["30S ribosomal protein S12    HP1197", "P0A0X4", "Q21632262", "NP_207988"]
            var template = _.template(
                "<div class='main-data'><h5>Protein Name: </h5> <a target='_blank' href='http://purl.uniprot.org/uniprot/<%= uniprot %>'><%= name %></a></div>" +
                "<div class='main-data'><h5>UniProt ID:   </h5> <a target='_blank' href='http://purl.uniprot.org/uniprot/<%= uniprot %>'><%= uniprot %></a></div>" +
                "<div class='main-data'><h5>Wikidata ID:  </h5> <a target='_blank' href='https://www.wikidata.org/wiki/<%= qid %>'><%= qid %></a></div>" +
                "<div class='main-data'><h5>RefSeq ID:    </h5> <a target='_blank' href='http://www.ncbi.nlm.nih.gov/protein/<%= refseq %>'><%= refseq %></a></div>"
            );
            this.$protD.html(template(data));
        }

    };

    var goData = {
        init: function (uniprot) {
            this.cacheDOM();
            this.goTermData(uniprot);

        },
        goTermData: function (uniprot) {

            getGOTerms(uniprot, function (goTerms) {
                //console.log(goTerms);
                goData.render(goTerms);
            });

        },
        cacheDOM: function () {
            this.$go = $('#goBoxes');
            this.$mf = this.$go.find('#molfuncdata');
            this.$bp = this.$go.find('#bioprocdata');
            this.$cc = this.$go.find('#celcompdata');
            this.$molTab = $('#mfTab');
            this.$biopTab = $('#bpTab');
            this.$celcTab = $('#ccTab');
        },
        generate_go_template: function (terms, refid) {
            var data = {
                'label': terms['gotermValueLabel']['value'],
                'goid': terms['goID']['value'],
                'evi_url': terms['determination']['value'],
                'evi_label': terms['determinationLabel']['value'],
                'referenceID': refid
            };

            var go_template = _.template(
                "<div class=\"row main-dataul\">" +
                "<div class=\"col-xs-5\"><h5><%= label %></h5></div>" +
                "<div class=\"col-xs-3\">" +
                "<a target=\"_blank\" href=http://amigo.geneontology.org/amigo/term/<%= goid %>><h5><%= goid %></h5></a></div>" +
                "<div class=\"col-xs-2\">" +
                "<a target=\"_blank\" href='<%= evi_url %>'><h5><%= evi_label %></h5></a></div>" +
                "<div id='main-ref-button'class=\"col-xs-2\">" +
                "<button type='button' id=<%= referenceID %> class='main-button-ref btn btn-default div-ref-but' ></button></div>" +
                "</div>" +
                "</div>");
            return (go_template(data))
        },
        pmidRef: function (button, results) {
            if (results.hasOwnProperty('pmid')) {
                //console.log(results['pmid']['value']);
                goRefModal_obj.init(button, results['reference_stated_inLabel']['value'],
                    results['reference_retrievedLabel']['value'], results['pmid']['value']);
                //
            } else {
                //console.log('hello');
                goRefModal_obj.init(button, results['reference_stated_inLabel']['value'],
                    results['reference_retrievedLabel']['value'], 'None');
            }
        },
        render: function (goTerms) {
            var $molf = this.$mf;
            $molf.html('');
            var $biop = this.$bp;
            $biop.html('');
            var $celc = this.$cc;
            $celc.html('');
            var ecNumbers = {};

            var nodata = {
                'gotermValueLabel': {'value': 'No Data Available'},
                'goID': {'value': '--------'},
                'determination': {'value': ''},
                'determinationLabel': {'value': '---'},
                'referenceID': {'value': ''}
            };
            this.$molTab.text('Molecular Function (' + goTerms['molecularFunction'].length + ')');
            this.$biopTab.text('Biological Process (' + goTerms['biologicalProcess'].length + ')');
            this.$celcTab.text('Cellular Component (' + goTerms['cellularComponent'].length + ')');

            if (goTerms['molecularFunction'].length > 0) {
                $.each(goTerms['molecularFunction'], function (key, element) {
                    var godat = goData.generate_go_template(element, "mf_" + key);
                    $molf.append(godat);
                    var $refbut = $molf.find('#mf_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        if (element['ecnumber']['value'].indexOf('-') > -1) {

                        }
                        else {
                            ecNumbers[element['ecnumber']['value']] = {
                                'ec': element['ecnumber']['value'],
                                'statedIn': element['reference_stated_inLabel']['value'],
                                'retrieved': element['reference_retrievedLabel']['value']
                            };
                        }
                    }
                });

            } else {
                $molf.html(goData.generate_go_template(nodata, 'mf_' + ' '));
            }
            if (goTerms['biologicalProcess'].length > 0) {
                $.each(goTerms['biologicalProcess'], function (key, element) {
                    var godat = goData.generate_go_template(element, 'bp_' + key);
                    $biop.append(godat);
                    var $refbut = $biop.find('#bp_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        if (element['ecnumber']['value'].indexOf('-') > -1) {

                        }
                        else {
                            ecNumbers[element['ecnumber']['value']] = {
                                'ec': element['ecnumber']['value'],
                                'statedIn': element['reference_stated_inLabel']['value'],
                                'retrieved': element['reference_retrievedLabel']['value']
                            };
                        }
                    }

                });
            } else {
                $biop.html(goData.generate_go_template(nodata, 'bp_' + ' '));

            }
            if (goTerms['cellularComponent'].length > 0) {
                $.each(goTerms['cellularComponent'], function (key, element) {
                    var godat = goData.generate_go_template(element, 'cc_' + key);
                    $celc.append(godat);
                    var $refbut = $celc.find('#cc_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        if (element['ecnumber']['value'].indexOf('-') > -1) {

                        }
                        else {
                            ecNumbers[element['ecnumber']['value']] = {
                                'ec': element['ecnumber']['value'],
                                'statedIn': element['reference_stated_inLabel']['value'],
                                'retrieved': element['reference_retrievedLabel']['value']
                            };
                        }
                    }
                });

            } else {
                $celc.html(goData.generate_go_template(nodata, 'cc_' + ' '));
            }

            //var uniqueECs = _.uniq(ecNumbers, false);

            $('#ezTab').text('Enzyme Class (' + Object.keys(ecNumbers).length + ')');

            if (Object.keys(ecNumbers).length > 0) {
                $.each(ecNumbers, function (key, element) {
                    EnzClassData.init(element);
                });
            }
            else {
                EnzClassData.init('None');
            }

        }

    };

    var EnzClassData = {
        init: function (ecNumber) {
            this.cacheDOM();
            this.$ecnum.html('');
            if (ecNumber != 'None') {
                this.reactionData(ecNumber);
            }
            else {
                this.render('None', 'None');
            }

        },
        cacheDOM: function () {

            this.$ecnum = $('#enzymeprodata');
            this.$ezTab = $('#ezTab');
        },
        generate_ec_template: function (ecnumber, reaction) {
            var data = {
                'ecnumber': ecnumber,
                'ecselector': ecnumber.replace(/\./g, ''),
                'reaction': reaction
            };
            var ec_template = _.template(
                "<div class='row main-dataul'>" +
                "<div class='col-xs-2'><h5><%= ecnumber %></h5></div>" +
                "<div class='col-xs-8'><a href='http://enzyme.expasy.org/EC/<%= ecnumber %>.txt'><%= reaction %></a></div>" +
                "<div id='main-ref-button'class='col-xs-2'>" +
                "<button type='button' id='<%= ecselector %>' class='main-button-ref btn btn-default div-ref-but' ></button></div>" +
                "</div></div>");
            return (ec_template(data))

        },
        reactionData: function (ecNumber) {
            console.log(ecNumber);
            getReaction(ecNumber['ec'], function (rxnData) {
                EnzClassData.render(ecNumber['ec'], rxnData);
                ecRefModal_obj.init(ecNumber);
            });

        },
        render: function (ecNumber, reaction) {
            var $enz = this.$ecnum;
            console.log(ecNumber);
            console.log(reaction);
            $enz.append(EnzClassData.generate_ec_template(ecNumber, reaction['reactions']));


        }


    };

    var interProData = {
        init: function (uniprot) {
            this.cacheDOM();
            this.$ipData.html('');
            this.interProtData(uniprot);


        },
        interProtData: function (uniprot) {
            getInterPro(uniprot, function (ipDomains) {
                interProData.render(ipDomains);
            });

        },
        cacheDOM: function () {
            this.$ipData = $('#interprodata');
            this.$ipTab = $('#ipTab');

        },
        render: function (ipDomains) {
            this.$ipTab.text('InterPro Domains (' + ipDomains['InterPro'].length + ')');
            var ipD = this.$ipData;
            if (ipDomains['InterPro'].length > 0) {
                $.each(ipDomains['InterPro'], function (key, element) {
                    ipD.append(interProData.ipInput(element['interPro_label']['value'], element['ipID']['value']));
                    interProRefModal_obj.init(ipD, element['reference_stated_inLabel']['value'], element['refURL']['value']);
                    //console.log(element['reference_stated_inLabel']['value']);

                });
            }
            else {
                ipD.html(interProData.ipInput("No InterPro Domain Data Available", '---------'));
            }

        },
        ipInput: function (iplable, ipid) {
            return "<div class=\"row main-dataul\"><div class=\"col-xs-5\"><h5>" +
                iplable + "</h5></div>" +
                "<div class=\"col-xs-3\"><h5>" + ipid + "</h5></a></div>" +
                "<div class=\"col-xs-2\"><h5></h5></a></div>" +
                "<div id='main-ref-button' class=\"col-xs-2\"> <button type='button' class='main-button-ref btn btn-default div-ref-but' ></button></div>" +
                "</div>";
        }
    };

    var operonData = {
        init: function (entrez) {
            this.cacheDOM();
            this.$opData.html('');
            this.$opGenes.html('');
            this.$opTab.text("Operon (0)");
            this.operonData(entrez);
            this.operonIdentifier(entrez);
        },
        operonIdentifier: function (entrez) {
            getOperon(entrez, function (operon) {
                if (operon['Operon'].length > 0) {
                    operonData.renderOP(operon);
                }
            });
        },
        operonData: function (entrez) {
            getOperonData(entrez, function (operonGenes) {
                if (operonGenes['Operon'].length > 0) {
                    operonData.renderOPGenes(operonGenes);
                }

            });
        },
        cacheDOM: function () {
            this.$opTab = $('#opTab');
            this.$opBox = $('#operonBox');
            this.$opData = this.$opBox.find('#operondata');
            this.$opGenes = this.$opBox.find('#operonGenesdata');
        },
        generate_operon_template: function (operon_identifier) {
            var wdid = operon_identifier['Operon'][0]['operonItem']['value'].split("/");
            var operonQID = wdid.slice(-1)[0];
            var data = {
                'operon_label': operon_identifier['Operon'][0]['operonItemLabel']['value'],
                'operon_wduri': operon_identifier['Operon'][0]['operonItem']['value'],
                'operon_qid': operonQID
            };

            var op_template = _.template(
                '<h3 class="dat-space-bottom main-data" style="padding-bottom: 3px"><%= operon_label %></h3>'

                //"<div style='margin-bottom: 10px' class='row main-data'>" +
                //"<div class='col-xs-8'><%= operon_label %></div> " +
                //"<div class='col-xs-2'><a target='_blank' href='<%= operon_wduri %>'><%= operon_qid %> </a></div> " +
                //"<div id='main-ref-button' class=\"col-xs-2\"> <button type='button' class='main-button-ref btn btn-default div-ref-but' ></button></div>" +
                //"</div>"
            );
            return (op_template(data));
        },
        generate_opGenes_template: function (operon_genes) {
            var wdid = operon_genes['gene']['value'].split("/");
            var geneQID = wdid.slice(-1)[0];


            var strandQID = operon_genes['strand']['value'];
            var data = {
                'gene': operon_genes['op_genes']['value'],
                'geneQID': geneQID,
                'gene_label': operon_genes['op_genesLabel']['value'],
                'genStart': operon_genes['genStart']['value'],
                'genEnd': operon_genes['genEnd']['value'],
                'entrez': operon_genes['entrez']['value'],
                'locus_tag': operon_genes['locusTag']['value'],
                'strandQID': strandQID
            };

            if (strandQID === 'http://www.wikidata.org/entity/Q22809711') {
                data['strand'] = 'Reverse';
            }
            else {
                data['strand'] = 'Forward';
            }

            var op_gene_template = _.template(
                "<div class='row main-annotations main-data'>" +
                "<div class='col-xs-4' ><%= gene_label %></div>" +
                "<div class='col-xs-1'><a target='_blank' href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= entrez %>'><%= entrez %></a></div>" +
                "<div class='col-xs-1'><a target='_blank' href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= locus_tag %>'><%= locus_tag %></a></div>" +
                "<div class='col-xs-1'><a target='_blank' href='<%= gene %>'><%= geneQID %></a></div>" +
                "<div class='col-xs-1'><%= genStart %></div>" +
                "<div class='col-xs-1'><%= genEnd %></div>" +
                "<div class='col-xs-2'><%= strand %></div>" +
                "<div class='col-xs-1' id='main-ref-button'> <button type='button' class='main-button-ref btn btn-default div-ref-but' ></button></div>" +
                "</div>"
            );
            return (op_gene_template(data));
        },

        renderOP: function (operon) {
            console.log(operon);
            this.$opTab.text("Operon (1)");
            var opD = this.$opData;
            console.log(opD);
            this.$opData.html(this.generate_operon_template(operon));
            operonRefModal_obj.init(opD, operon.Operon[0]['reference_stated_inLabel']['value'], operon.Operon[0]['reference_stated_in']['value'],  operon.Operon[0]['reference_pmid']['value']);
        },

        renderOPGenes: function (operonGenes) {
            //console.log(operonGenes);
            var opGD = this.$opGenes;
            $.each(operonGenes['Operon'], function (key, element) {
                //console.log(element);
                operonData.$opGenes.append(operonData.generate_opGenes_template(element));
                console.log(operonGenes);
                operonRefModal_obj.init(opGD, element['reference_stated_inLabel']['value'], element['reference_stated_in']['value'],  element['reference_pmid']['value']);

            });

        }


    };

///////////////////////////////////////End data rendering modules///////////////////////////////////////////////////////
// /////////////////////////////////////Begin reference modules///////////////////////////////////////////////////////

    var geneRefModal_obj = {
        init: function (geneData) {
            this.cacheDom();
            this.openModal(geneData);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdGeneRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refRetrieved = this.$modal.find('#main-ref-retrieved');

        },
        openModal: function (geneData) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $retrieved = this.$refRetrieved;
            //console.log(element.find('.div-ref-but'));
            $('#genPosRef').on('click', function () {
                //console.log("clicking ref button");
                $stated.html("<span><a href='http://www.ncbi.nlm.nih.gov/gene/?term=" + geneData[1] + "'><h5>NCBI Gene</h5></a>");
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

    var goRefModal_obj = {
        init: function (element, stated_in, retrieved, pmid) {
            this.cacheDom();
            this.openModal(element, stated_in, retrieved, pmid);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdGoRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refRetrieved = this.$modal.find('#main-ref-retrieved');
            this.$pmid = this.$modal.find('#main-ref-pmid');

        },
        openModal: function (element, stated_in, retrieved, pmid) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $retrieved = this.$refRetrieved;
            var $pmid = this.$pmid;

            console.log(element.find('.div-ref-but'));
            element.on('click', function () {
                //console.log("clicking ref button");
                $stated.html(stated_in);
                $retrieved.html(retrieved);
                $pmid.html(pmid);
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

    var ecRefModal_obj = {
        init: function (enzData) {
            this.cacheDom();
            this.openModal(enzData);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdECRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refRetrieved = this.$modal.find('#main-ref-retrieved');


        },
        openModal: function (enzData) {
            console.log(enzData);
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $retrieved = this.$refRetrieved;
            var $element = $('#' + enzData['ec'].replace(/\./g, ''));
            var stated_in = enzData['statedIn'];
            var retrieved = enzData['retrieved'];

            $element.on('click', function () {
                $stated.html(stated_in);
                $retrieved.html(retrieved);
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

    var interProRefModal_obj = {
        init: function (element, stated_in, refurl) {
            //console.log("interp ref obj thingy");
            this.cacheDom();
            this.openModal(element, stated_in, refurl);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdIPRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');

            this.$refURL = this.$modal.find('#main-ref-url');

        },
        openModal: function (element, stated_in, refurl) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $refURL = this.$refURL;

            element.find('.div-ref-but').on('click', function () {
                //console.log("clicking ref button");
                $stated.html(stated_in);
                $refURL.html(refurl);
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

    var operonRefModal_obj = {
        init: function (element, stated_in, qid, PMID) {
            //console.log("interp ref obj thingy");
            this.cacheDom();
            this.openModal(element, stated_in, qid, PMID);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdOPRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refPMID = this.$modal.find("#main-ref-PMID");


        },
        openModal: function (element, stated_in, qid, PMID) {
            console.log(PMID);
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $PMID = this.$refPMID;

            element.find('.div-ref-but').on('click', function () {
                //console.log("clicking ref button");
                $stated.html("<a href='" + qid + "'>" + stated_in + "</a>");
                $PMID.html("<a href='https://www.ncbi.nlm.nih.gov/pubmed/" + PMID + "'>" + PMID + "</a>");
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

/////////////////////////////////////////End reference modules//////////////////////////////////////////////////////////

//////////////////////////////////////////Begin JBrowse Module//////////////////////////////////////////////////////////

    var jbrowse = {
        init: function (taxid, refseq, coords, name) {
            this.cacheDOM();
            this.render(taxid, refseq, coords, name);

        },
        url: "/static/cmod_main/JBrowse-1.12.1/index.html?data=sparql_data/sparql_data_",
        coordPrefix: "&tracks=genes_canvas_mod,operons_canvas_mod&menu=0&loc=",
        cacheDOM: function () {
            this.$jb = $("#jbrowseModule");
            this.$browser = this.$jb.find('#jbrowse');
            this.$orgTitle = this.$jb.find('#main-organism-name');
            this.$name = this.$orgTitle.find('i');

        },
        render: function (taxid, refseq, coords, name) {
            var data = {
                'url': this.url + taxid + this.coordPrefix + refseq + coords,
                'name': name
            };
            this.$browser.html("<iframe src=\"" + data.url + "\"><iframe>");
            this.$name.html(name);
            //console.log(data.url);
        }


    };

/////////////////////////////////////////////////End Jbrowse module/////////////////////////////////////////////////////
// ///////////////////////////////////////////////Begin Authentication module///////////////////////////////////////////

    var getCookie = function (name) {
        console.log('testing getCookie');
        console.log('name');
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };
// ///////////////////////////////////////////////End Authentication module///////////////////////////////////////////
/////////////////////////////////////////////////Begin Wikidata API/////////////////////////////////////////////////////


    var oauth_authorization = {
        init: function () {
            this.buttonStatus();
            this.cacheDOM();
            this.initiateOAuth();


        },
        cacheDOM: function () {
            var $authButton = $('#wd-oauth-button');
        },
        initiateOAuth: function () {
            $('#wd-oauth-button').off("click").click(function (e) {
                e.preventDefault();
                oauth_authorization.sendToServer({"oauth": "True"}, '/wd_oauth');
            });

        },
        sendToServer: function (data, urlsuf) {
            var csrftoken = getCookie('csrftoken');
            $.ajax({
                type: "POST",
                url: window.location.pathname + urlsuf,
                data: data,
                dataType: 'json',
                headers: {'X-CSRFToken': csrftoken},
                success: function (data) {
                    console.log("OAuth Handshake Success:" + data);

                    window.location.replace(data);
                },
                error: function (data) {
                    console.log("Error");
                }
            });
        },
        buttonStatus: function () {
            if (verified === 'True') {
                var $Button = $('#wd-oauth-button');
                $Button.text("Authorized").addClass(".btn-success");
            }
        }


    };
    oauth_authorization.init();
/////////////////////////////////////////////////End Wikidata API///////////////////////////////////////////////////////
    var annotations = {
        annotations_data: {},
        annotations_list: [],
        annotations_list_list: [],
        endpoint: "https://query.wikidata.org/sparql?format=json&query=",
        init: function (taxid) {
            this.taxid = taxid;
            this.annotations_list_list = [];
            this.getGeneOntologyCounts("Molecular Function");
            this.getGeneOntologyCounts("Cellular Component");
            this.getGeneOntologyCounts("Biological Process");
            this.getChildEntityCounts("Genes");
            this.getChildEntityCounts("Proteins");
            this.getOperonCounts();
            this.getInterProCounts();
            this.getECNumberCounts();


            //console.log(annotations.annotations_data);
            //console.log(annotations.annotations_list);

        },

        getChildEntityCounts: function (enttype) {
            var entqids = {
                "Genes": "Q7187",
                "Proteins": "Q8054",
                "Operons": "Q139677"
            };

            var queryentity = "SELECT (count (distinct ?entity) as ?entity_counts) " +
                "WHERE { ?strain wdt:P685 '" + this.taxid + "'. " +
                "?entity wdt:P703 ?strain; wdt:P279 wd:" + entqids[enttype] + ".} GROUP BY ?strain";


            $.ajax({
                type: "GET",
                url: annotations.endpoint + queryentity,
                dataType: 'json',
                success: function (data) {
                    var dataDict = {
                        "label": enttype,
                        "value": 0
                    };
                    var dataList = [enttype];
                    if (data['results']['bindings'].length > 0) {
                        dataDict["value"] = data['results']['bindings'][0]['entity_counts']['value'];
                        annotations.annotations_list.push(dataDict);
                        annotations.annotations_data[enttype] = data['results']['bindings'][0]['entity_counts']['value'];
                    }
                    else {
                        annotations.annotations_data[enttype] = 0;
                        annotations.annotations_list.push(dataDict);
                    }
                }
            });
        },
        getOperonCounts: function () {
            var entqids = {
                "Operons": "Q139677"
            };

            var queryentity = "SELECT (count (distinct ?entity) as ?entity_counts) " +
                "WHERE { ?strain wdt:P685 '" + this.taxid + "'. " +
                "?entity wdt:P703 ?strain; wdt:P279 wd:" + entqids["Operons"] + ".} GROUP BY ?strain";


            $.ajax({
                type: "GET",
                url: annotations.endpoint + queryentity,
                dataType: 'json',
                success: function (data) {
                    //console.log("OperonSuccess");
                    var dataDict = {
                        "label": "Operons",
                        "value": 0
                    };
                    var dataList = ["Operons"];
                    if (data['results']['bindings'].length > 0) {
                        dataDict["value"] = data['results']['bindings'][0]['entity_counts']['value'];
                        annotations.annotations_list.push(dataDict);
                        annotations.annotations_data["Operons"] = data['results']['bindings'][0]['entity_counts']['value'];

                        dataList.push(parseInt(data['results']['bindings'][0]['entity_counts']['value']));
                    }
                    else {
                        annotations.annotations_data["Operons"] = 0;
                        annotations.annotations_list.push(dataDict);
                        dataList.push(0);
                    }
                    annotations.annotations_list_list.push(dataList);
                    annotations.renderChart(annotations.annotations_list_list);
                }
            });
        },


        getGeneOntologyCounts: function (goclass) {
            var goprops = {
                "Molecular Function": "P680",
                "Cellular Component": "P681",
                "Biological Process": "P682"
            };
            var queryMolFunc = "SELECT (count (distinct ?protein) as ?protein_counts) " +
                "WHERE { ?strain wdt:P685 '" + this.taxid + "'. " +
                "?protein wdt:P703 ?strain; wdt:P279 wd:Q8054; wdt:" + goprops[goclass] + " ?molfunc.} GROUP BY ?strain";


            $.ajax({
                type: "GET",
                url: annotations.endpoint + queryMolFunc,
                dataType: 'json',
                success: function (data) {
                    var dataDict = {
                        "label": goclass,
                        "value": 0
                    };
                    var dataList = [goclass];
                    if (data['results']['bindings'].length > 0) {
                        annotations.annotations_data[goclass] = data['results']['bindings'][0]['protein_counts']['value'];
                        dataDict["value"] = data['results']['bindings'][0]['protein_counts']['value'];
                        annotations.annotations_list.push(dataDict)
                        dataList.push(parseInt(data['results']['bindings'][0]['protein_counts']['value']));
                    }
                    else {
                        annotations.annotations_data[goclass] = 0;
                        annotations.annotations_list.push(dataDict);
                        dataList.push(0);
                    }
                    annotations.annotations_list_list.push(dataList);
                    annotations.renderChart(annotations.annotations_list_list);
                }
            });
        },
        getInterProCounts: function () {
            var queryMolFunc = "SELECT (count (distinct ?protein) as ?protein_counts) " +
                "WHERE { ?strain wdt:P685 '" + this.taxid + "'. " +
                "?protein wdt:P703 ?strain; " +
                "wdt:P279 wd:Q8054; " +
                "wdt:P527 ?hasPart. " +
                "?hasPart wdt:P2926 ?interproID. } " +
                "GROUP BY ?strain";


            $.ajax({
                type: "GET",
                url: annotations.endpoint + queryMolFunc,
                dataType: 'json',
                success: function (data) {
                    var dataDict = {
                        "label": "IP",
                        "value": 0
                    };
                    var dataList = ["InterPro"];
                    if (data['results']['bindings'].length > 0) {
                        annotations.annotations_data['InterPro'] = data['results']['bindings'][0]['protein_counts']['value'];
                        dataDict["value"] = data['results']['bindings'][0]['protein_counts']['value'];
                        annotations.annotations_list.push(dataDict);
                        dataList.push(parseInt(data['results']['bindings'][0]['protein_counts']['value']));
                    }
                    else {
                        annotations.annotations_data['InterPro'] = 0;
                        annotations.annotations_list.push(dataDict);
                        dataList.push(0);
                    }
                    annotations.annotations_list_list.push(dataList);
                    annotations.renderChart(annotations.annotations_list_list);
                }
            });
        },
        getECNumberCounts: function () {
            var queryEC = "SELECT (count (distinct ?protein) as ?protein_counts) " +
                "WHERE { ?strain wdt:P685 '" + this.taxid + "'. " +
                "?protein wdt:P703 ?strain; " +
                "{?protein wdt:P680 ?goterm.} " +
                "UNION{?protein wdt:P681 ?goterm.} " +
                "UNION{?protein wdt:P681 ?goterm.}  " +
                "?goterm wdt:P591 ?ecnumber. }";


            $.ajax({
                type: "GET",
                url: annotations.endpoint + queryEC,
                dataType: 'json',
                success: function (data) {
                    var dataDict = {
                        "label": "EC",
                        "value": 0
                    };
                    var dataList = ['EC Number'];
                    if (data['results']['bindings'].length > 0) {
                        annotations.annotations_data['ECNumber'] = data['results']['bindings'][0]['protein_counts']['value'];
                        dataDict["value"] = data['results']['bindings'][0]['protein_counts']['value'];
                        annotations.annotations_list.push(dataDict);
                        dataList.push(parseInt(data['results']['bindings'][0]['protein_counts']['value']));
                    }
                    else {
                        annotations.annotations_data['ECNumber'] = 0;
                        annotations.annotations_list.push(dataDict);
                        dataList.push(0);
                    }
                    annotations.annotations_list_list.push(dataList);
                    annotations.renderChart(annotations.annotations_list_list);
                }
            });
        },
        renderGenesProteins: function (data) {
            //console.log(data['Genes'], data['Proteins']);
            $('#genecount').html("<span>" + data['Genes'] + "</span>");
            $('#proteincount').html("<span>" + data['Proteins'] + "</span>");


        },
        renderChart: function (dataSet) {
            // Load the Visualization API and the corechart package.
            google.charts.load('current', {'packages': ['corechart']});

            // Set a callback to run when the Google Visualization API is loaded.
            google.charts.setOnLoadCallback(drawChart);

            // Callback that creates and populates a data table,
            // instantiates the pie chart, passes in the data and
            // draws it.
            function drawChart() {

                // Create the data table.
                var data = new google.visualization.DataTable();
                data.addColumn('string', 'Entity');
                data.addColumn('number', 'Entities');
                data.addRows(dataSet);

                // Set chart options

                var options = {
                    width: '100%',
                    height: '100%',
                    legend: 'none',
                    bar: {groupWidth: '95%'},
                    vAxis: {
                        gridlines: {count: 4},
                    },
                    hAxis: {
                        textStyle: {
                            bold: true,
                            fontSize: 7
                        },
                        slantedText: true,
                        slantedTextAngle: 45,
                        textPosition: 'out'

                    },
                    chartArea: {left: '10%', width: '75%', height: '65%'}
                };


                // Instantiate and draw our chart, passing in some options.
                var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));

                chart.draw(data, options);
                function resizeChart() {
                    chart.draw(data, options);
                }

                if (document.addEventListener) {
                    window.addEventListener('resize', resizeChart);
                }
                else if (document.attachEvent) {
                    window.attachEvent('onresize', resizeChart);
                }
                else {
                    window.resize = resizeChart;
                }
                annotations.renderGenesProteins(annotations.annotations_data);
            }

        }

    };


////////////////////////////////////////////////////Begin preload///////////////////////////////////////////////////////

    orgData.init(currentTaxa);
    geneForm.init(currentTaxa['Taxid']);
    annotations.init(currentTaxa['Taxid']);
//////////////////////////////////////////////////////End data preload//////////////////////////////////////////////////

/////////////////////////////////////////////////////Experimental /////////////////////////////////////////////////

/////////////////////////////////////////////////////Experimental /////////////////////////////////////////////////


});

