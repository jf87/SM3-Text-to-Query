# Attribution 

Directory Attribution: 
`./synthea-rdf-converter-fork/` - Forked from  [SYNTHEA RDF - Semantic web representation for the Synthea](https://github.com/leroykim/synthea-rdf)

Original work by Dae-young Kim under GNU General Public License v3.0


The `synthea-rdf-converter-fork` directory was directly forked from the `synthea-rdf` github repository (https://github.com/leroykim/synthea-rdf) by Dae-young Kim.

In a second step the configuration file was adjusted for the SM3 project, such that the underlying Synthea CSV files could directly be converted and integrated into the GraphDB database.

The changes in the conversion file include: 
- adjustment of the synthea data location 
- definition of a temporary location of the resulting ttl files 
- addition of a function, which clears old temporary files before adding new ones
- direct integration of the conversion file into the automated `setup-graphdb.py` file