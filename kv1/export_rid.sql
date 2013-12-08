﻿\COPY line (operator_id, publiccode, name) TO '/tmp/openebs_lines.csv' WITH CSV HEADER;
\COPY stoppoint (operator_id, name, latitude, longitude) TO '/tmp/openebs_stops.csv' WITH CSV HEADER;
COPY (SELECT DISTINCT j.privatecode as journey_id, j.departuretime as base_departure_time, p.directiontype as direction
 FROM servicejourney as j JOIN journeypattern as p on (j.journeypatternref = p.id)
 WHERE j.privatecode like 'HTM:%' ORDER BY direction, journey_id) TO '/tmp/openebs_journeys.csv' WITH CSV HEADER;
/* With times: \COPY (SELECT j.privatecode as journey_id, j.departuretime as base_departure_time, p.directiontype as direction, p_pt.pointorder as stop_sequence, s_pt.operator_id as userstopcode, departuretime+totaldrivetime as arrival_time, departuretime+totaldrivetime+stopwaittime as departure_time, iswaitpoint as timepoint FROM servicejourney as j JOIN journeypattern as p on (j.journeypatternref = p.id)                          JOIN pointinjourneypattern as p_pt on (p_pt.journeypatternref = p.id) JOIN pointintimedemandgroup as t_pt on (j.timedemandgroupref = t_pt.timedemandgroupref AND p_pt.pointorder = t_pt.pointorder) JOIN scheduledstoppoint as s_pt ON (s_pt.id = pointref) WHERE j.privatecode like 'HTM:%' ORDER BY direction, journey_id, stop_sequence) TO '/tmp/openebs_journey_stops.csv' WITH CSV HEADER; */
\COPY (SELECT privatecode, validdate FROM servicejourney JOIN availabilityconditionday USING (availabilityconditionref) WHERE privatecode like 'HTM:%' and isavailable = true and validdate > 'yesterday') TO '/tmp/openebs_journey_dates.csv' WITH CSV HEADER;