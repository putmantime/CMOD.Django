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
        acsource: function (orginput) {
            getOrgs(function (orgTags) {
                orginput.autocomplete({
                    minLength: 0,
                    source: orgTags,
                    autoFocus: true,

                    select: function (event, ui) {

                        $('form').each(function () {
                            this.reset()
                        });
                        orginput.val("");
                        $("#geneData, #protData, .main-go-data").html("");

                        currentTaxa = {
                            'Name': ui.item.label,
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
                        item.label + "</strong></u></i><br>Taxid: " + item.taxid + "<br>Wikidata: " +
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
                            ui.item.label,
                            ui.item.id,
                            ui.item.gqid,
                            ui.item.locustag,
                            ui.item.genomicstart,
                            ui.item.genomicend
                        ];
                        this.currentProtein = [
                            ui.item.proteinLabel,
                            ui.item.uniprot,
                            ui.item.protein,
                            ui.item.refseqProtein

                        ];

                        //get GO Terms for this gene/protein
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
                        .append("<div class='main-data' style=\"border-bottom: solid black 1px\"><strong><u>" + item.label +
                        "</u></strong><br>Entrez ID:" + item.id + "<br>Wikidata: " + item.gqid + "</div>")
                        .appendTo(ul);
                };
                var first_gene = [
                    geneTags[0].label,
                    geneTags[0].id,
                    geneTags[0].gqid,
                    geneTags[0].locustag,
                    geneTags[0].genomicstart,
                    geneTags[0].genomicend
                ];
                var first_protein = [
                    geneTags[0].proteinLabel,
                    geneTags[0].uniprot,
                    geneTags[0].protein,
                    geneTags[0].refseqProtein

                ];
                geneData.init(first_gene);
                proteinData.init(first_protein);
                goData.init(first_protein[1]);
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
            this.$radiobutton.click(function () {
                var radioValue = $("input[name='optradio']:checked").parent().text();
                if (radioValue) {
                    goFormAll.goFormData["goClass"] = radioValue;

                }
            });

        },
        editWD: function () {
            this.$editWDButton.on("click", function (e) {
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
                        alert("Could not login");
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
            this.$tid.html("<span><h4>NCBI Taxonomy ID:</h4>" + data['organism']['Taxid'] + "</span>");
            this.$qid.html("<span><h4>Wikidata Item ID</h4>" + data['organism']['QID'] + "</span>");
            this.$rsid.html("<span><h4>NCBI RefSeq ID</h4>" + data['organism']['RefSeq'] + "</span>");

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


            this.template = this.$gd.find('#gene-template').html();

        },
        render: function (gene) {
            //console.log(gene);
            var data = {
                'gene': gene
            };
            //console.log(data.gene[1]);

            this.$geneD.html(
                "<div class='main-data'> <h5>Gene Name:    </h5>     " + data.gene[0] + "</div>" +
                "<div class='main-data'> <h5>Entrez ID:    </h5> <a href='http://www.ncbi.nlm.nih.gov/gene/?term=" + data.gene[1] + "'>" + data.gene[1] + "</a></div>" +
                "<div class='main-data'> <h5>Wikidata ID:  </h5> <a href='https://www.wikidata.org/wiki/" + data.gene[2] + "'>" + data.gene[2] + "</a></div>" +
                "<div class='main-data'> <h5>Locus Tag:    </h5> <a href='http://www.ncbi.nlm.nih.gov/gene/?term=" + data.gene[3] + "'>" + data.gene[3] + "</a></div>" +
                "<div class='main-data'> <h5>Genomic Start:</h5>     " + data.gene[4] + "</div>" +
                "<div class='main-data'> <h5>Genomic End:  </h5>     " + data.gene[5] + "</div>"
            );


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
                'protein': protein
            };


            this.$protD.html(
                "<div class='main-data'><h5>Protein Name: </h5>" + data.protein[0] + "</div>" +
                "<div class='main-data'><h5>UniProt ID:   </h5>" + data.protein[1] + "</div>" +
                "<div class='main-data'><h5>Wikidata ID:  </h5>" + data.protein[2] + "</div>" +
                "<div class='main-data'><h5>RefSeq ID:    </h5>" + data.protein[3] + "</div>"
            );
        }

    };

//////render the gene ontology data in the GO boxes//////
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

        },
        render: function (goTerms) {
            //console.log(goTerms);
            var mf = this.$mf;
            var bp = this.$bp;
            var cc = this.$cc;
            if (goTerms['molecularFunction'].length > 0) {
                $.each(goTerms['molecularFunction'], function (key, element) {
                    mf.append(goData.goInput(element['goterm_label']['value'], element['goID']['value']));
                    //console.log("mf" + element['goterm_label']['value']);
                });
            } else {
                mf.append(goData.goInput("No Molecular Function Data Available", "----------"));
            }
            if (goTerms['biologicalProcess'].length > 0) {
                $.each(goTerms['biologicalProcess'], function (key, element) {
                    bp.append(goData.goInput(element['goterm_label']['value'], element['goID']['value']));
                    //console.log("bp" + element['goterm_label']['value']);
                });
            } else {
                bp.append(goData.goInput("No Biological Process Data Available", "----------"));
            }
            if (goTerms['cellularComponent'].length > 0) {
                $.each(goTerms['cellularComponent'], function (key, element) {
                    cc.append(goData.goInput(element['goterm_label']['value'], element['goID']['value']));
                    //console.log("cc" + element['goterm_label']['value']);
                });
            } else{
                cc.append(goData.goInput("No Cellular Component Data Available", "----------"));
            }
        },
        goInput: function (golable, goid) {
            return "<div class=\"row main-dataul\"><div class=\"col-md-8\"><h5>" +
                golable + "</h5></div>" +
                "<div class=\"col-md-4\">" +
                "<a target=\"_blank\" href=http://amigo.geneontology.org/amigo/term/" + goid + "><h5>" +
                goid + "</h5></a>" +
                "</div></div>";
        }
    };

    var interProData = {
        init: function (uniprot) {
            console.log("interpro init" + uniprot);
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
            this.$ipData = this.$ip.find('#interpordata');

        },
        render: function (ipDomains) {
            var ipD = this.$ipData;
            if (ipDomains['InterPro'].length > 0) {
                console.log(ipDomains['InterPro']);
                console.log("its alive");

                $.each(ipDomains['InterPro'], function (key, element) {
                    console.log(element);
                    console.log(element['interPro_label']['value']);

                    ipD.append(interProData.ipInput(element['interPro_label']['value'], element['ipID']['value']));
                });
            }
            else {
                ipD.append(interProData.ipInput("No InterPro Domain Data Available", '---------'));
            }
        },
        ipInput: function (iplable, ipid) {
            return "<div class=\"row main-dataul\"><div class=\"col-md-8\"><h5>" +
                iplable + "</h5></div>" +
                "<div class=\"col-md-4\">" +
                "<a target=\"_blank\" href=http://amigo.geneontology.org/amigo/term/" + ipid + "><h5>" +
                ipid + "</h5></a>" +
                "</div></div>";
        }
    };
///////////////////////////////////////End data rendering modules///////////////////////////////////////////////////////


//////////////////////////////////////////Begin JBrowse Module//////////////////////////////////////////////////////////

    var jbrowse = {

        init: function (taxid, refseq, coords, name) {
            this.cacheDOM();
            this.render(taxid, refseq, coords, name);

        },
        url: "../../static/cmod_main/JBrowse-1.12.1-dev/index.html?data=sparql_data/sparql_data_",
        coordPrefix: "&tracklist=0&menu=0&loc=",
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


    //var djangoServer = {
    //    init: function (data, urlsuf) {
    //        this.sendToServer(data, urlsuf);
    //        console.log("attempting to send data to server");
    //
    //    },
    //    sendToServer: function (data, urlsuf) {
    //        var csrftoken = this.getCookie('csrftoken');
    //        $.ajax({
    //            type: "POST",
    //            url: window.location.pathname + urlsuf,
    //            data: data,
    //            dataType: 'json',
    //            headers: {'X-CSRFToken': csrftoken},
    //            success: function (data) {
    //                console.log("success");
    //                console.log(data);
    //                //alert("Successful interaction with the server");
    //
    //            },
    //            error: function (data) {
    //                console.log("error");
    //                console.log(data);
    //                //alert("Something went wrong interacting with the server");
    //            }
    //        });
    //    },
    //    getCookie: function (name) {
    //        var cookieValue = null;
    //        if (document.cookie && document.cookie !== '') {
    //            var cookies = document.cookie.split(';');
    //            for (var i = 0; i < cookies.length; i++) {
    //                var cookie = jQuery.trim(cookies[i]);
    //                // Does this cookie string begin with the name we want?
    //                if (cookie.substring(0, name.length + 1) === (name + '=')) {
    //                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
    //                    break;
    //                }
    //            }
    //        }
    //        return cookieValue;
    //    }
    //};


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
            this.$loginButton = this.$loginForm.find('#editWDButton');
            this.$loggedin = $('#userLogin');


        },
        sendCredentials: function () {

            wdLogin.$loginButton.on("click", function (e) {
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
                        $("#userLogin").html("<h5>" + "Logged in as " + data['userName']);
                    }
                    else {

                        $("#userLogin").html("<h5>" + "Could not log in. Please try again");
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
    jbrowse.init(currentTaxa['Taxid'], currentTaxa['RefSeq'], ':100000..200000&tracks=genes_canvas_mod', currentTaxa['Name']);
    orgData.init(currentTaxa);
    geneForm.init(currentTaxa['Taxid']);
    //geneData.init([
    //    '2-oxoglutarate dehydrogenase complex subunit dihydrolipoyllysine-residue succinyltransferase CTL0311',
    //    '5858187',
    //    'http://www.wikidata.org/entity/Q21168910',
    //    'CTL0311',
    //    '385948',
    //    '387045'
    //]);
    //
    //proteinData.init([
    //    '2-oxoglutarate dehydrogenase complex subunit dihydrolipoyllysine-residue succinyltransferase CTL0311',
    //    'A0A0H3MBK1',
    //    'http://www.wikidata.org/entity/Q21172795',
    //    'YP_001654394'
    //]);
    //goData.init('A0A0H3MBK1');
//////////////////////////////////////////////////////End data preload//////////////////////////////////////////////////
});

