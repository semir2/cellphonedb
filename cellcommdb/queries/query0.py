import pandas as pd

from cellcommdb.extensions import db
from cellcommdb.models import Protein, Multidata, Gene, Interaction


class Query0:
    @staticmethod
    def call(counts_df, meta_df):
        print('Excuting query 0')

        gene_protein_query = db.session.query(Gene, Protein, Multidata).join(Protein).join(Multidata)
        gene_protein_df = pd.read_sql(gene_protein_query.statement, db.engine)

        multidata_counts = pd.merge(counts_df, gene_protein_df, left_on='Gene', right_on='ensembl')

        print('Reduging A: Receptor or Adhesion')
        # A:  Reduce matrix: All Receptors & Adhesion
        count_receptor_adhesion = multidata_counts[
            (multidata_counts['receptor'] == True) | (multidata_counts['adhesion'] == True)]

        print('Reduced A: Receptor or Adhesion')
        print('Reducing B1: interacting_ligands ')

        # B: Reduce Matrix: All possible interacting Ligands

        # B.1: Is membarane not other not transporter or secreted

        interacting_ligands = multidata_counts[((multidata_counts['transmembrane'] == True) &
                                                (multidata_counts['other'] == False) &
                                                (multidata_counts['transporter'] == False)) |
                                               (multidata_counts['secretion'] == True)]

        print('Reduced B1: interacting_ligands ')
        print('Reducing B2: interacting_ligands (receptor interactings)')
        # B.2 Is interacting with a receptor
        interactions_df = Query0._get_interactions()

        def interacting_with_receptor(count):
            return (interactions_df[interactions_df['name_1'] == count['name']]['receptor_2'].any() or
                    interactions_df[interactions_df['name_2'] == count['name']]['receptor_1'].any())

        interacting_ligands = interacting_ligands[
            interacting_ligands.apply(interacting_with_receptor, axis=1)]
        print('Reduced B2: interacting_ligands (receptor interactings)')

        # Merge two lists
        filtered_counts = interacting_ligands.append(count_receptor_adhesion)

        print('Removing duplicates')
        filtered_counts = filtered_counts[filtered_counts.duplicated('ensembl') == False]

        return Query0._procesed_table(filtered_counts, meta_df, 0)

    @staticmethod
    def _procesed_table(counts, meta_df, threshold):

        clusters_names = meta_df[meta_df.duplicated('cell_type') == False]['cell_type']
        print('Creating data for procesed table')
        procesed_data = []
        for index, count in counts.iterrows():

            positive_cells = 0
            clusters_data = []
            for cluster_name in clusters_names:
                for index, cell_name in meta_df[meta_df['cell_type'] == cluster_name].iterrows():
                    if count[cell_name.values[0]]:
                        positive_cells = positive_cells + 1

                clusters_data.append({'cluster_name': cluster_name,
                                      'positive_cells': positive_cells,
                                      'number_cells': len(meta_df[meta_df['cell_type'] == cluster_name])})

            procesed_data.append({'gene': count['ensembl'],
                                  'clusters': clusters_data
                                  })

        results_data = []

        print('Creating procesed table and calculating numbers')
        for data in procesed_data:
            result_row = {}
            result_row['gene'] = data['gene']

            for cluster in data['clusters']:
                result_row[cluster['cluster_name']] = cluster['positive_cells'] / cluster['number_cells']

            results_data.append(result_row)

        result_df = pd.DataFrame(results_data)

        return result_df

    @staticmethod
    def _get_interactions():
        interactions_query = db.session.query(Interaction)
        interactions_df = pd.read_sql(interactions_query.statement, db.engine)

        multidata_query = db.session.query(Multidata)
        multidata_df = pd.read_sql(multidata_query.statement, db.engine)

        interactions_df.drop('id', axis=1, inplace=True)

        interactions_df = pd.merge(interactions_df, multidata_df, left_on=['multidata_1_id'], right_on=['id'])
        interactions_df = pd.merge(interactions_df, multidata_df, left_on=['multidata_2_id'], right_on=['id'],
                                   suffixes=['_1', '_2'])

        return interactions_df
