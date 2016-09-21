$(document).ready(function () {
//////////////////////////////////////////Begin Global variables////////////////////////////////////////////////////////
    var currentTaxa = {
        "Name": OrgName,
        "Taxid": OrgTID,
        "QID": OrgQID,
        "RefSeq": OrgRefSeq
    };


///////////////////////////////////////////End Global Variables/////////////////////////////////////////////////////////
///////////////////////////////////////////Begin form modules///////////////////////////////////////////////////////////
//////organism selection form module//////
    var orgForm = {

        init: function () {
            this.cacheDOM();
            this.acsource(this.$input);

        },
        cacheDOM: function () {
            this.$of = $("#orgFormModule");
            this.$input = this.$of.find('input');


        },
        // populate organism form with list of bacteria to choose from
        acsource: function (orginput) {
            getOrgs(function (orgTags) {
                orginput.autocomplete({
                    minLength: 0,
                    source: orgTags, //sparql query callback
                    autoFocus: true,

                    select: function (event, ui) {

                        $('form').each(function () {
                            this.reset()
                        });
                        orginput.val("");
                        $("#geneData, #protData, .main-go-data").html("");

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
                        //launch jbrowse
                        jbrowse.init(
                            currentTaxa.Taxid,
                            currentTaxa.RefSeq,
                            ":100000..200000&tracks=genes_canvas_mod",
                            currentTaxa.Name
                        );
                        //if (window.location.pathname == '/CMOD/') {
                        //    console.log(currentTaxa.Name);
                        //    window.location.replace('/CMOD/main_page')
                        //}
                        if (window.location.pathname === '/CMOD/') {
                            location.href = "main_page.html?id=" + currentTaxa.Taxid;

                        }
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
                        $("#geneData, #protData, .main-go-data").html("");
                        geneinput.val("");

                        this.currentGene = [
                            ui.item.name,
                            ui.item.id,
                            ui.item.gqid,
                            ui.item.locustag,
                            ui.item.genomicstart,
                            ui.item.genomicend,
                            ui.item.strand,
                            currentTaxa[3]
                        ];
                        console.log(ui.item.strand);
                        this.currentProtein = [
                            ui.item.proteinLabel,
                            ui.item.uniprot,
                            ui.item.protein,
                            ui.item.refseqProtein

                        ];

                        //get GO Terms for this gene/protein
                        //goData.init(this.currentProtein[1]);
                        goData.init(this.currentProtein[1]);
                        interProData.init(this.currentProtein[1]);
                        //Render the data into the gene and protein boxes
                        geneData.init(this.currentGene);
                        proteinData.init(this.currentProtein);
                        //initialize the goform
                        //console.log(this.currentProtein[2]);
                        goFormAll.init(this.currentProtein[2]);
                        //focus jbrowse on selected gene
                        var gstart = this.currentGene[4] - 400;
                        var gend = this.currentGene[5] - (-400);
                        jbrowse.init(currentTaxa.Taxid, currentTaxa.RefSeq, ":" + gstart + ".." + gend, currentTaxa.Name);
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
                var first_gene = [
                    geneTags[0].name,
                    geneTags[0].id,
                    geneTags[0].gqid,
                    geneTags[0].locustag,
                    geneTags[0].genomicstart,
                    geneTags[0].genomicend,
                    geneTags[0].strand

                ];
                var first_protein = [
                    geneTags[0].proteinLabel,
                    geneTags[0].uniprot,
                    geneTags[0].protein,
                    geneTags[0].refseqProtein

                ];
                //initialize all modules on organism load
                geneData.init(first_gene);

                proteinData.init(first_protein);
                interProData.init(first_protein[1]);
                //goData.init(first_protein[1]);
                goData.init(first_protein[1]);
                goFormAll.init(first_protein[2]);
                var gstart = first_gene[4] - 400;
                var gend = first_gene[5] - (-400);
                //console.log(gend);
                jbrowse.init(currentTaxa.Taxid, currentTaxa.RefSeq, ":" + gstart + ".." + gend, currentTaxa.Name);
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
            this.evidenceCodesAC();
            this.pmidForm();
            this.goClassRadio();
            this.editWD();


        },
        cacheDOM: function () {
            this.$goTermForm = $('#main-go-form');
            this.$goForm = this.$goTermForm.find('#goTermForm');
            this.$goEviForm = this.$goTermForm.find('#eviCodeForm');
            this.$pmidForm = this.$goTermForm.find('#pmidForm');
            this.$radiobutton = this.$goTermForm.find('#go-radio');
            this.$editWDButton = this.$goTermForm.find('#editWDButton');
        },
        goTermsAC: function () {
            this.$goForm.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: goFormAll.endpoint + ["SELECT DISTINCT ?goTerm ?goTermLabel ?goID WHERE { ?goTerm wdt:P686 ?goID.",
                            "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". ?goTerm rdfs:label ?goTermLabel.}",
                            "FILTER(CONTAINS(LCASE(?goTermLabel), \"" + request.term + "\"))}"].join(" "),
                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['results']['bindings'], function (key, element) {
                                var wdid = element['goTerm']['value'].split("/");
                                var orgqid = wdid.slice(-1)[0];
                                data_hash = {
                                    'label': element['goTermLabel']['value'],
                                    'value': orgqid,
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


                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>Gene Ontology ID:" + item.id + "<br>Wikidata: " + item.qid + "</div>")
                    .appendTo(ul);
            };
        },
        evidenceCodesAC: function () {
            this.$goEviForm.autocomplete({
                delay: 900,
                autoFocus: true,
                minLength: 3,
                appendTo: null,
                source: function (request, response) {
                    $.ajax({
                        type: "GET",
                        url: goFormAll.endpoint + [
                            "select distinct ?evidence_code ?evidence_codeLabel ?alias where {" +
                            "?evidence_code wdt:P31 wd:Q23173209. " +
                            "?evidence_code skos:altLabel ?alias." +
                            "filter (lang(?alias) = \"en\") " +
                            "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\" .}",
                            "FILTER(CONTAINS(LCASE(?alias), \"" + request.term + "\"))}"
                        ].join(" "),


                        datatype: 'json',
                        success: function (data) {
                            var data_array = [];
                            var data_hash = {};
                            $.each(data['results']['bindings'], function (key, element) {
                                var wdid = element['evidence_code']['value'].split("/");
                                var evqid = wdid.slice(-1)[0];
                                data_hash = {
                                    'label': element['alias']['value'],
                                    'value': evqid,
                                    'id': element['evidence_codeLabel']['value'],
                                    'qid': evqid

                                };
                                data_array.push(data_hash);
                            });
                            response(data_array);
                        }
                    });
                },
                select: function (event, ui) {
                    goFormAll.goFormData["evidenceCode"] = ui.item.qid;
                }
            })
                .autocomplete("instance")._renderItem = function (ul, item) {
                return $("<li>")
                    .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                    "</u></strong><br>Evidence Code: " + item.id + "<br>Wikidata: " + item.qid + "</div>")
                    .appendTo(ul);
            };
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
                        url: 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + request.term,
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
                    goFormAll.goFormData["PMID"] = ui.item.id;
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
        goClassRadio: function () {
            var $radbutton = this.$radiobutton;
            $radbutton.click(function () {

                var radVal = $("input[name='optradio']:checked").val();
                console.log(radVal);
                //var radioValue = $("input[name='optradio']:checked").parent().text();
                if (radVal) {
                    goFormAll.goFormData["goClass"] = radVal;

                }
            });

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
                        alert("Wikidata item succesfully edited!\nIt may take a few minutes for it to show up here.")
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
            //this.templateORG = this.$od.find('#org-template').html();
            //console.log($('#org-template').html());

        },
        render: function (taxData) {

            var data = {
                'organism': taxData,
                'thing': 'thing'
            };
            this.$tid.html("<span><h5>NCBI Taxonomy ID:</h5>" + data['organism']['Taxid'] + "</span>");
            this.$qid.html("<span><h5>Wikidata Item ID</h5>" + data['organism']['QID'] + "</span>");
            this.$rsid.html("<span><h5>NCBI RefSeq ID</h5>" + data['organism']['RefSeq'] + "</span>");

        }
    };
//////render the gene data in Gene box//////
    var geneData = {
        init: function (gene) {
            this.cacheDOM();
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
            console.log(gene[6]);
            if (gene[6] === 'http://www.wikidata.org/entity/Q22809711') {
                data['strand'] = 'Reverse';
            }
            else {
                data['strand'] = 'Forward';
            }

            //console.log(data);
            var template = _.template(
                "<div class='main-data'> <h5>Gene Name: </h5><a href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= entrez %>'><%= name %></a> </div>" +
                "<div class='main-data'> <h5>Entrez ID: </h5> <a href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= entrez %>'><%= entrez %></a></div>" +
                "<div class='main-data'> <h5>Wikidata ID: </h5> <a href='https://www.wikidata.org/wiki/<%= qid %>'><%= qid %></a></div>" +
                "<div class='main-data'> <h5>NCBI Locus Tag: </h5> <a href='http://www.ncbi.nlm.nih.gov/gene/?term=<%= locus_tag %>'><%= locus_tag %></a></div>" +
                "<div class='main-data'> <h5>Genomic Start: </h5> <%= gen_start %></div>" +
                "<div class='main-data'> <h5>Genomic End: </h5> <%= gen_end %></div>" +
                "<div class='main-data'> <h5>Genomic Strand: </h5> <%= strand %></div>"
            );
            this.$geneD.html(template(data));
            geneRefModal_obj.init(this.$annotations, '-------', '-------');
        }
    };
//////render the protein dat in the Protein box///////
    var proteinData = {
        init: function (protein) {
            this.cacheDOM();
            this.render(protein);

        },
        cacheDOM: function () {
            this.$pd = $("#proteinDataModule");
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
            console.log(protein); //["30S ribosomal protein S12    HP1197", "P0A0X4", "Q21632262", "NP_207988"]
            var template = _.template(
                "<div class='main-data'><h5>Protein Name: </h5><a href='http://purl.uniprot.org/uniprot/<%= uniprot %>'><%= name %></a></div>" +
                "<div class='main-data'><h5>UniProt ID:   </h5> <a href='http://purl.uniprot.org/uniprot/<%= uniprot %>'><%= uniprot %></a></div>" +
                "<div class='main-data'><h5>Wikidata ID:  </h5> <a href='https://www.wikidata.org/wiki/<%= qid %>'><%= qid %></a></div>" +
                "<div class='main-data'><h5>RefSeq ID:    </h5> <a href='http://www.ncbi.nlm.nih.gov/protein/<%= refseq %>'><%= refseq %></a></div>"
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
            this.$tabs = $('#annotations-tabs');

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
                "<div class=\"col-md-5\"><h5><%= label %></h5></div>" +
                "<div class=\"col-md-3\">" +
                "<a target=\"_blank\" href=http://amigo.geneontology.org/amigo/term/<%= goid %>><h5><%= goid %></h5></a></div>" +
                "<div class=\"col-md-2\">" +
                "<a target=\"_blank\" href='<%= evi_url %>'><h5><%= evi_label %></h5></a></div>" +
                "<div id='main-ref-button'class=\"col-md-2\">" +
                "<button type='button' id=<%= referenceID %> class='main-button-ref btn btn-primary div-ref-but' ></button></div>" +
                "</div>" +
                "</div>");
            return (go_template(data))
        },
        pmidRef: function (button, results) {
            if (results.hasOwnProperty('pmid')) {
                //console.log(results['pmid']['value']);
                goRefModal_obj.init(button, results['reference_stated_inLabel']['value'],
                    results['reference_retrievedLabel']['value'], results['pmid']['value'], results['goID']['value']);
                //
            } else {
                //console.log('hello');
                goRefModal_obj.init(button, results['reference_stated_inLabel']['value'],
                    results['reference_retrievedLabel']['value'], 'None', results['goID']['value']);
            }
        },
        render: function (goTerms) {
            console.log(goTerms);
            var $molf = this.$mf;
            var $biop = this.$bp;
            var $celc = this.$cc;
            var $enzclass = this.$ecnum;

            if (goTerms['molecularFunction'].length > 0) {
                $.each(goTerms['molecularFunction'], function (key, element) {
                    var godat = goData.generate_go_template(element, "mf_" + key);
                    $molf.append(godat);
                    var $refbut = $molf.find('#mf_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        EnzymeData.init(element);
                    }
                });
            } else {
                $molf.append("<div class='main-data'><h5>No Molecular Function Data Available</h5></div>");
            }
            if (goTerms['biologicalProcess'].length > 0) {
                $.each(goTerms['biologicalProcess'], function (key, element) {
                    var godat = goData.generate_go_template(element, 'bp_' + key);
                    $biop.append(godat);
                    var $refbut = $biop.find('#bp_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        EnzymeData.init(element);
                    }

                });
            } else {
                $biop.append("<div class='main-data'><h5>No Biological Process Data Available</h5></div>");
            }
            if (goTerms['cellularComponent'].length > 0) {
                $.each(goTerms['cellularComponent'], function (key, element) {
                    var godat = goData.generate_go_template(element, 'cc_' + key);
                    $celc.append(godat);
                    var $refbut = $celc.find('#cc_' + key);
                    goData.pmidRef($refbut, element);
                    if (element.hasOwnProperty("ecnumber")) {
                        EnzymeData.init(element);
                    }
                });
            } else {
                $celc.append("<div class='main-data'><h5>No Cellular Component Data Available</h5></div>");
            }
        }

    };

    var EnzymeData = {
        init: function (gotermData) {
            this.cacheDOM();
            this.render(gotermData);
        },
        cacheDOM: function () {
            this.$ec = $('#enzymeBoxes');
            this.$ecnum = this.$ec.find('#enzymeprodata');
        },
        generate_ec_template: function (terms) {
            var data = {
                'ecnumber': terms['ecnumber']['value']

            };
            var ec_template = _.template("<div class='row main-dataul'><div class='col-md-2'><h5><%= ecnumber %></h5></div>" +
                "<div class='col-md-4'></div>" +
                "<div class='col-md-2'></div>" +
                "<div class='col-md-2'></div>" +
                "<div id='main-ref-button'class='col-md-2'>" +
                "<button type='button' id='<%= ecnumber %>' class='main-button-ref btn btn-primary div-ref-but' ></button></div>" +
                "</div></div>");
            return (ec_template(data))

        },
        render: function (gotermData) {
            console.log(gotermData);
            var $enz = this.$ecnum;

            var ectemplate = this.generate_ec_template(gotermData);
            $enz.html(ectemplate);

        }
    };

    var interProData = {
        init: function (uniprot) {
            //console.log("interpro init" + uniprot);
            this.cacheDOM();
            this.interProtData(uniprot);

        },
        interProtData: function (uniprot) {
            getInterPro(uniprot, function (ipDomains) {
                interProData.render(ipDomains);
            });

        },
        cacheDOM: function () {
            this.$ip = $('#interProBoxes');
            this.$ipData = this.$ip.find('#interprodata');

        },
        render: function (ipDomains) {
            var ipD = this.$ipData;
            if (ipDomains['InterPro'].length > 0) {
                //console.log(ipDomains['InterPro']);
                //console.log("its alive");

                $.each(ipDomains['InterPro'], function (key, element) {
                    //console.log(element);
                    //console.log(element['interPro_label']['value']);

                    ipD.append(interProData.ipInput(element['interPro_label']['value'], element['ipID']['value']));
                    interProRefModal_obj.init(ipD, element['reference_stated_inLabel']['value'], element['pubDate']['value'],
                        element['version']['value'], element['refURL']['value']);
                });
            }
            else {
                ipD.append(interProData.ipInput("No InterPro Domain Data Available", '---------'));
            }
        },
        ipInput: function (iplable, ipid) {
            return "<div class=\"row main-dataul\"><div class=\"col-md-5\"><h5>" +
                iplable + "</h5></div>" +
                "<div class=\"col-md-3\"><h5>" + ipid + "</h5></a></div>" +
                "<div class=\"col-md-2\"><h5></h5></a></div>" +
                "<div id='main-ref-button' class=\"col-md-2\"> <button type='button' class='main-button-ref btn btn-primary div-ref-but' ></button></div>" +
                "</div>";
        }
    };


///////////////////////////////////////End data rendering modules///////////////////////////////////////////////////////
// /////////////////////////////////////Begin reference modules///////////////////////////////////////////////////////

    var geneRefModal_obj = {
        init: function (element, stated_in, retrieved) {
            this.cacheDom();
            this.openModal(element, stated_in, retrieved);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdGeneRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refRetrieved = this.$modal.find('#main-ref-retrieved');

        },
        openModal: function (element, stated_in, retrieved) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $retrieved = this.$refRetrieved;
            //console.log(element.find('.div-ref-but'));
            element.find('.div-ref-but').on('click', function () {
                //console.log("clicking ref button");
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

    var goRefModal_obj = {
        init: function (element, stated_in, retrieved, pmid, coreid) {
            this.cacheDom();
            this.openModal(element, stated_in, retrieved, pmid, coreid);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdGoRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refRetrieved = this.$modal.find('#main-ref-retrieved');
            this.$pmid = this.$modal.find('#main-ref-pmid');
            this.$core_id = this.$modal.find('#main-ref-coreid');

        },
        openModal: function (element, stated_in, retrieved, pmid, coreid) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $retrieved = this.$refRetrieved;
            var $pmid = this.$pmid;
            var $coreid = this.$core_id;

            //console.log(element.find('.div-ref-but'));
            element.on('click', function () {
                console.log("clicking ref button");
                $stated.html(stated_in);
                $retrieved.html(retrieved);
                $pmid.html(pmid);
                $coreid.html(coreid);
                $modal.modal('show');
            });
        },
        closeModal: function () {

            this.$modalClose.on('click', function () {

            });
        }

    };

    var interProRefModal_obj = {
        init: function (element, stated_in, pubdate, version, refurl) {
            this.cacheDom();
            this.openModal(element, stated_in, pubdate, version, refurl);
            this.closeModal();
        },
        cacheDom: function () {
            this.$modal = $('#wdIPRefModal');
            this.$modalClose = this.$modal.find('#modalRefClose');
            this.$refStated = this.$modal.find('#main-ref-statedin');
            this.$refPubDate = this.$modal.find('#main-ref-pubDate');
            this.$refVersion = this.$modal.find('#main-ref-version');
            this.$refURL = this.$modal.find('#main-ref-url');

        },
        openModal: function (element, stated_in, pubdate, version, refurl) {
            var $modal = this.$modal;
            var $stated = this.$refStated;
            var $pubdate = this.$refPubDate;
            var $refVersion = this.$refVersion;
            var $refURL = this.$refURL;

            element.find('.div-ref-but').on('click', function () {
                //console.log("clicking ref button");
                $stated.html(stated_in);
                $pubdate.html(pubdate);
                $refVersion.html(version);
                $refURL.html(refurl);

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
        url: "/static/cmod_main/JBrowse-1.12.1-dev/index.html?data=sparql_data/sparql_data_",
        coordPrefix: "&tracklist=0&tracks=genes_canvas_mod&menu=0&loc=",
        cacheDOM: function () {
            this.$jb = $("#jbrowseModule");
            this.$browser = this.$jb.find('#jbrowse');
            this.$orgTitle = this.$jb.find('#main-organism-name');
            this.$name = this.$orgTitle.find('i');

            this.templateJB = this.$jb.find('#jbrowse-template').html();


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
    var wdLogin = {
        init: function () {
            this.cacheDOM();
            this.sendCredentials();


        },
        cacheDOM: function () {
            this.$loginForm = $('#main-login-form');
            this.$userName = this.$loginForm.find('#wduserName');
            this.$password = this.$loginForm.find('#wdPassword');
            this.$editButton = this.$loginForm.find('#editWDButton');
            this.$loginButtonDiv = $('#wd-login-button-div');
            this.$loginButton = this.$loginButtonDiv.find('#wd-login-button');
            this.$loggedin = $('#userLogin');


        },
        sendCredentials: function () {

            wdLogin.$editButton.on("click", function (e) {
                e.preventDefault();
                var credentials = {
                    "userName": wdLogin.$userName.val(),
                    "password": wdLogin.$password.val()
                };
                wdLogin.sendToServer(credentials, '/wd_credentials');

                $('form').each(function () {
                    this.reset()
                });
            });

        },
        sendToServer: function (data, urlsuf) {
            var csrftoken = getCookie('csrftoken');
            $.ajax({
                beforeSend: function () {
                    wdLogin.$loggedin.html("<img src=" + loader + ">");

                },
                type: "POST",
                url: window.location.pathname + urlsuf,
                data: data,
                dataType: 'json',
                headers: {'X-CSRFToken': csrftoken},
                success: function (data) {
                    console.log("success");
                    //console.log(data);
                    if (data['login'] === "success") {
                        wdLogin.$loggedin.html("<h5>" + "Logged in as " + data['userName'] + "</h5>");
                        wdLogin.$loginButtonDiv.html(
                            "<button id='wd-logout-button' type='button' class='btn btn-primary'> " +
                            "<span>Log out</span> </button>");
                        $('#wd-logout-button').off("click").click(function (e) {
                            wdLogin.$loggedin.html("");
                            wdLogin.$loginButtonDiv.html(
                                "<button id='wd-login-button' type='button' class='btn btn-primary' " +
                                "data-toggle='modal' data-target='#wdLoginModal'> <span>Login to Wikidata</span> </button>");
                        });


                    }
                    else {

                        $("#userLogin").html("<h5>Could not log in. Please try again</h5>");
                    }

                },
                error: function (data) {
                    console.log("error");
                    //console.log(data);
                    //alert("Something went wrong interacting with the server");
                }
            });
        }

    };

    wdLogin.init();
/////////////////////////////////////////////////End Wikidata API///////////////////////////////////////////////////////


////////////////////////////////////////////////////Begin preload///////////////////////////////////////////////////////

    orgData.init(currentTaxa);
    geneForm.init(currentTaxa['Taxid']);
//////////////////////////////////////////////////////End data preload//////////////////////////////////////////////////

/////////////////////////////////////////////////////Experimental /////////////////////////////////////////////////

/////////////////////////////////////////////////////Experimental /////////////////////////////////////////////////


});

