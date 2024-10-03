"""
Voorbeeld discreet:
- Studenten van een land met studienummers
- Omdat studienummers serieel worden uitgegeven, kan je een regel toepassen om studenten te groepen op welke regels voor hen gelden/golden
- Voorbeelden: financieel (kosten studie, lening vs gift studiebeurs), studievoorwaarden (BSA, maximale lengte studie), naam van titel (Doctorandus vs Master, Doctor vs PhD), en vast nog wel meer.
- Doel: je geeft een set aan voorwaarden op die je wil combineren en je krijgt de studenten die aan elk van die voorwaarden voldoen -> IntervalSet
- Doel: je geeft een studentnummer op en je krijgt per voorwaarde of de leerling daartoe behoort
- Doel: studenten identificeren die op de grens zitten voor een interview
- Doel: studenten identificeren die de meest negatieve situaties combineren
- Twist: lijstje met studenten die een uitzondering vormen (bijv eerder ingeschreven maar nooit begonnen en daardoor een lager nummer) -> splitsen van Intervals.
"""
from intervalues import IntervalList

"""
This example concerns keeping track of which student regulations apply to which students at a university or college.
This works on the basis of student numbers being granted serially (with exceptions, see below), so in general, if there
is a new regulation in place, it will apply to all students starting from a specific number. Of course, we use discrete
intervals for this, since student numbers are discrete numbers.

To give a bit more context of the type of regulations these could be (in case this example does not apply to how this
is structured in your country), I would be thinking of regulations like:
- financial (costs of studying; whether the study grant is a loan or a gift; additional costs for a 2nd Bachelor/Master)
- requirements (how much time you have for the first year or the entire Bachelor)
- name of granted title (currently Bachelor, Master, etc; but there used to be country specific titles before)
- other benefits (free public transport)

The benefits of intervalues in this case are that (without additional effort) the restrictions can be combined in a 
memory-efficient way: you only need to know all the bounds. Then you can plug in student numbers ("123456 in x") as if
it is a full list of students.

Exceptions to this "serial" property of student numbers could arise in practice. For example, some students could have
registered in an earlier year as potential students, getting a student number in the mean time, but last minute decided
to postpone their study for whatever reason. One could still use `intervalues` for this, but apply these exceptions as
well, either within `intervalues` by using more granular intervals (with these exceptions as single-point intervals),
or afterwards by first ignoring the exceptions and then filtering them from any list or use-case later on.
"""
from random import randint
import intervalues as iv


# Generate the regulations and which students are impacted by it
# In this case, the regulations are all single-cutoffs, but that does not need to be the case of course.
nr_students = 999999
nr_regulations = 50
regulations_cutoff = [randint(1, nr_students) for _ in range(nr_regulations)]
positive = [randint(0, 1) == 1 for _ in range(nr_regulations)]  # A regulation change could be positive or negative
positive[12] = True  # For example below
positive[27] = False
regulations_cutoff[12], regulations_cutoff[27] = (max([regulations_cutoff[12], regulations_cutoff[27]]),
                                                  min([regulations_cutoff[12], regulations_cutoff[27]]))

intervals_positive = [iv.BaseDiscreteInterval(1, cutoff - 1) if not positive[i] else
                      iv.BaseDiscreteInterval(cutoff, nr_students)
                      for i, cutoff in enumerate(regulations_cutoff)]
intervals_negative = [iv.BaseDiscreteInterval(1, cutoff - 1) if positive[i] else
                      iv.BaseDiscreteInterval(cutoff, nr_students)
                      for i, cutoff in enumerate(regulations_cutoff)]


# Question: which students are negatively impacted by regulations 12 or 27? (zero-indexed)
selected_intervals = [intervals_negative[12], intervals_negative[27]]
impacted = iv.combine_intervals_set_discrete([intervals_negative[12], intervals_negative[27]])
print(f'Negatively impacted by either regulation 12 or 27: numbers {impacted.min()} to {impacted.max()}')

# Question: which students are negatively impacted by regulations 12 and 27? (zero-indexed)
impacted = iv.combine_intervals_counter_discrete([intervals_negative[12], intervals_negative[27]])
impacted_twice = [k for k, v in impacted.items() if v == 2][0]
print(f'Negatively impacted by either regulation 12 or 27: numbers {impacted_twice.min()} to {impacted_twice.max()}')

# Question: how many regulations are positively impacting student 456123?
counter = iv.combine_intervals_counter_discrete(intervals_positive)
print(f'Student 456123 is positively impacted by {counter[456123]} regulations')

# Question: which ones are they?
print('The regulations positively affecting student 456123 are: ' + ", ".join([str(i)
    for i, interval in enumerate(intervals_positive) if 456123 in interval]))

# Question: How many students combine the most negative consequences, and how many consequences are those?
counter = iv.combine_intervals_counter_discrete(intervals_negative)
count_most = counter.most_common(1)[0][1]
students_count_most = [k for k, v in counter.items() if v == count_most]
print('The students that are most negative affected by all regulations are the following:')
[print(f" Number {k.start} to {k.stop}") for k in students_count_most]
print(f'They are affected by {count_most} regulations in a negative way')
