from SPARQLWrapper import SPARQLWrapper, JSON
import pprint
import psycopg2
from datetime import datetime


class UpdatePSQLDatabase(object):
    def __init__(self):

        try:
            self.conn = psycopg2.connect("dbname=CMOD user=timputman host='localhost'")
        except:
            print("nope")
        self.cur = self.conn.cursor()

    @staticmethod
    def execute_query(query):
        endpoint = SPARQLWrapper(endpoint="https://query.wikidata.org/sparql")
        wd = 'PREFIX wd: <http://www.wikidata.org/entity/>'
        wdt = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/>'
        endpoint.setQuery(query)
        endpoint.setReturnFormat(JSON)
        wd_query = endpoint.query().convert()
        return wd_query['results']['bindings']

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for c in range(0, len(l), n):
            yield l[c:c + n]

    def get_go_terms(self):
        goquery = '''
                        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                        PREFIX wd: <http://www.wikidata.org/entity/>
                        SELECT DISTINCT ?goTerm ?goTermLabel ?goID ?goclass ?goclassLabel WHERE {
                        ?goTerm wdt:P686 ?goID;
                                wdt:P279* ?goclass.
                        SERVICE wikibase:label {
                            bd:serviceParam wikibase:language "en".
                        }
                        FILTER ( ?goclass = wd:Q2996394 || ?goclass = wd:Q5058355 || ?goclass = wd:Q14860489)
                        }
                        '''
        goresults = self.execute_query(goquery)
        go_chunks = self.chunks(goresults, 100)
        res = 0
        for chunk in go_chunks:
            res += 1
            data_list = []
            for goterm in chunk:
                print('INSERT_' + str(res))
                goTermQid = goterm['goTerm']['value'].split("/")[-1]
                goClassQid = goterm['goclass']['value'].split("/")[-1]

                column_data = (goterm['goID']['value'], goTermQid, goterm['goTermLabel']['value'],
                               goClassQid, goterm['goclassLabel']['value'], str(datetime.now()))
                data_list.append(column_data)

            self.cur.executemany("""INSERT INTO goterms (id, goqid, golabel, coclassqid, goclasslabel, retrieved)
                                       VALUES (%s,%s,%s,%s,%s,%s)
                                       ON CONFLICT (id) DO UPDATE SET retrieved = CURRENT_TIMESTAMP ;""", data_list)
            self.conn.commit()

    def querydb(self):
        self.cur.execute("""SELECT * from goterms;""")
        rows = self.cur.fetchall()
        print(len(rows))
        return rows






