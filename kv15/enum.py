DATAOWNERCODE = (
    ('ARR', 'Arriva'),
    ('VTN', 'Veolia'),
    ('CXX', 'Connexxion'),
    ('EBS', 'EBS'),
    ('GVB', 'GVB'),
    ('HTM', 'HTM'),
    ('NS',  'Nederlandse Spoorwegen'),
    ('RET', 'RET'),
    ('SYNTUS', 'Syntus'),
    ('KEOLIS', 'Keolis'),
    ('QBUZZ', 'Qbuzz'),
    ('TCR', 'Taxi Centrale Renesse'),
    ('GOVI', 'GOVI'),
    ('WSF', 'Westerschelde Ferry')
)

MESSAGEPRIORITY = (
    ('CALAMITY', 'Calamiteit'),
    ('PTPROCESS', 'OV'),
    ('COMMERCIAL', 'Commercieel'),
    ('MISC', 'Overig'),
)

MESSAGETYPE = (
    ('GENERAL', 'Algemeen'),
    ('ADDITIONAL', 'Extra'),
    ('OVERRULE', 'Overschrijf'),
    ('BOTTOMLINE', 'Onderaan'),
)

MESSAGEDURATIONTYPE = (
    ('REMOVE', 'Verwijder'),
    ('FIRSTVEJO', 'Volgende rit'),
    ('ENDTIME', 'Eind Tijd'),
)

ADVICETYPE = (
    (0, 'Onbekend'),
    (1, 'Algemeen Advies'),
    (255, 'Ongedefineerd'),
)

SUBADVICETYPE = (
    ('0', 'geen'),
    ('1', 'niet reizen'),
    ('2', 'reizen met ander ov'),
    ('3_1', 'overstappen in'),
    ('3_2', 'reizen via'),
    ('3_3', 'in-/uitstappen'),
)

EFFECTTYPE = (
    (0, 'Onbekend'),
    (1, 'Algemeen Effect'),
    (255, 'Ongedefineerd'),
)

SUBEFFECTTYPE = (
    ('0', 'onbekend'),
    ('11', 'minder vervoer'),
    ('5', 'geen vervoer'),
    ('6', 'vervoer ontregeld'),
    ('5', 'geen treinen'),
    ('4', 'omleiding'),
    ('4_1', 'omleiding met vertraging'),
    ('3_1', 'vertraging onbekend'),
    ('3_2', 'vertraging 5 min.'),
    ('3_3', 'vertraging 10 min.'),
    ('3_4', 'vertraging 15 min.'),
    ('3_5', 'vertraging 30 min.'),
    ('3_6', 'vertraging 45 min.'),
    ('3_7', 'vertraging 60 min.'),
    ('3_8', 'vertraging 60 min. en meer'),
    ('3_9', 'vertraging 5 tot 10 min.'),
    ('3_10', 'vertraging 10 tot 15 min.'),
    ('3_11', 'vertraging 15 tot 30 min.'),
    ('3_12', 'vertraging 30 tot 60 min.'),
    ('5_1', 'vervallen halte(n)'),
    ('5_2', 'traject vervallen'),
)

MEASURETYPE = (
    (0, 'Onbekend'),
    (1, 'Algemene Maatregel'),
    (255, 'Ongedefineerd'),
)

SUBMEASURETYPE = (
    ('0', 'extra vervoer'),
    ('1', 'vervallen halte(n)'),
    ('2', 'vervangende halte(n)'),
    ('3', 'rijden via omweg'),
    ('4_1', 'geen businzet'),
    ('4_2', 'beperkte businzet'),
    ('4_3', 'businzet'),
    ('5_1', 'geen treinen'),
    ('5_2', 'minder treinen'),
    ('5_3', 'treinen rijden via'),
    ('6', 'geen'),
    ('7', 'route aangepast'),
)

REASONTYPE = (
    (0, 'Onbekend'),
    (1, 'Overig'),
    (2, 'Personeel'),
    (3, 'Materieel'),
    (4, 'Omgeving'),
    (255, 'Ongedefinieerd'),
)

SUBREASONTYPE = (
    ('255', 'Onbekend'),
    ('0_1', 'Eerdere verstoring'),
    ('11', 'Herstel werkzaamheden'),
    ('11_2', 'Uitloop herstelwerkzaamheden'),
    ('12', 'Stroomstoring'),
    ('12_1', 'Defecte bovenleiding'),
    ('12_2', 'Uitloop werkzaamheden'),
    ('14', 'Defecte brug'),
    ('14', 'Wateroverlast'),
    ('14_1', 'Defect viaduct'),
    ('15', 'File'),
    ('16', 'Route versperd'),
    ('16', 'Stremming'),
    ('17', 'Mensen op de route'),
    ('18', 'Auto in spoor'),
    ('19_1', 'Omgevallen bomen'),
    ('20', 'Vee op de route'),
    ('23', 'Werkzaamheden'),
    ('23_1', 'Rioleringswerkzaamheden'),
    ('23_2', 'Wegwerkzaamheden'),
    ('23_3', 'Asfalteringswerkzaamheden'),
    ('23_4', 'Bestratingswerkzaamheden'),
    ('24_1', 'Optocht'),
    ('24_10', 'Kermis'),
    ('24_11', 'Koniginnedag'),
    ('24_12', 'Marathon'),
    ('24_13', 'Wielerronde'),
    ('24_14', 'Voetbalwedstrijd'),
    ('24_15', 'Herdenking'),
    ('24_16', 'Avondvierdaagse'),
    ('24_6', 'Bloemencorso'),
    ('24_7', 'Braderie'),
    ('24_8', 'Carnaval'),
    ('24_9', 'Jaarmarkt'),
    ('26_1', 'Snelheidsbeperkingen'),
    ('26_2', 'Logistieke problemen'),
    ('3', 'Sneeuw'),
    ('3_1', 'Op last van de politie'),
    ('3_11', 'Ontruiming'),
    ('3_15', 'Ruimen WO II bom'),
    ('3_17', 'Op last van de brandweer'),
    ('3_9', 'Bommelding'),
    ('4', 'Brand'),
    ('4', 'Seinstoring'),
    ('4', 'Tekort aan personeel'),
    ('4_1', 'Sein en wisselstoring'),
    ('5', 'Ontsporing'),
    ('5', 'Staking'),
    ('5', 'Storm'),
    ('5', 'Vakbondsacties'),
    ('5_1', 'Mogelijke staking'),
    ('6', 'Ongeval'),
    ('6', 'Stiptheidsactie'),
    ('6_2', 'Defecte trein'),
    ('6_3', 'Aanrijding met een persoon'),
    ('6_4', 'Passagier onwel'),
    ('6_6', 'Aanrijding'),
    ('7', 'Defect materieel'),
    ('7', 'Extreme drukte'),
    ('8_1', 'Defect spoor'),
    ('8_4', 'Tekort aan materieel'),
    ('8_10', 'Wisselstoring'),
    ('8_11', 'Overwegstoring'),
    ('8_12', 'Storing in verkeersleidingsysteem'),
    ('8_13', 'Gladde sporen'),
    ('9', 'Herstelwerkzaamheden'),
    ('9_1', 'Gladheid'),
    ('9_2', 'IJsgang'),
    ('9_2', 'IJzel'),
    ('255', 'Weersomstandigheden'),
    ('255_1', 'Blikeminslag'),
)

# KV17
STOPTYPES = (
    ('FIRST', "Beginhalte"),
    ('INTERMEDIATE', "Tussenhalte"),
    ('LAST', "Eindhalte")
)
