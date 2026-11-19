# Approaches

The reference implementation gives each team a `TeamStats` object. That object
owns the team's counters, calculates its points, and formats its table row.
The tournament processes each result by updating both teams' objects.

Another option is to keep plain records in a `Map` keyed by team name. For every
match, update the two records, then sort the map entries by points and team
name before formatting the rows. A `win` for the first team increments its wins
and the second team's losses; a `loss` reverses those updates.

For example, `Allegoric Alaskans;Blithering Badgers;win` gives the Alaskans one
win and 3 points, and the Badgers one loss and 0 points. Writing the same result
as `Blithering Badgers;Allegoric Alaskans;loss` produces those same standings.
With no matches, either approach returns only the table header.

The class-based approach keeps team behavior and formatting together, which can
make the counters easier to understand as the exercise grows. The map approach
uses a compact data structure and separates updating records from formatting
rows, but it requires a map lookup for each team and can feel less familiar if
you have not used `Map` before. Neither approach needs to keep a separate
history of every match.
