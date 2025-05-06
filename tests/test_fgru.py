import pytest
from fgru import is_notable

@pytest.mark.parametrize("achievement, expected", [
    ({"Type": "Skill", "Skill": "Attack", "Xp": 200000000}, True),  # 200m XP in a skill
    ({"Type": "Skill", "Skill": "Attack", "Xp": 199999999}, False),  # Not 200m XP
    ({"Type": "Skill", "Skill": "Overall", "Xp": 1000000000}, True),  # 1b Overall XP
    ({"Type": "Skill", "Skill": "Overall", "Xp": 2000000000}, True),  # 2b Overall XP
    ({"Type": "Skill", "Skill": "Overall", "Xp": 4600000000}, True),  # 4.6b Overall XP
    ({"Type": "Skill", "Skill": "Overall", "Xp": 999999999}, False),  # Not 1b Overall XP
    ({"Type": "Skill", "Skill": "Ehp", "Xp": 1000}, True),  # 1,000 EHP
    ({"Type": "Skill", "Skill": "Ehp", "Xp": 2000}, True),  # 2,000 EHP
    ({"Type": "Skill", "Skill": "Ehp", "Xp": 999}, False),  # Not 1,000 EHP
    ({"Type": "Pvm", "Skill": "Sarachnis", "Xp": 1000}, False),  # Not Ehb, elite, master, or collections
    ({"Type": "Pvm", "Skill": "Ehb", "Xp": 1000}, True),  # 1,000 EHB
    ({"Type": "Pvm", "Skill": "Ehb", "Xp": 2000}, True),  # 2,000 EHB
    ({"Type": "Pvm", "Skill": "Ehb", "Xp": 999}, False),  # Not 1,000 EHB
    ({"Type": "Pvm", "Skill": "Clue_elite", "Xp": 1000}, True),  # 1,000 Elite Clues
    ({"Type": "Pvm", "Skill": "Clue_elite", "Xp": 2000}, True),  # 2,000 Elite Clues
    ({"Type": "Pvm", "Skill": "Clue_elite", "Xp": 999}, False),  # Not 1,000 Elite Clues
    ({"Type": "Pvm", "Skill": "Clue_master", "Xp": 1000}, True),  # 1,000 Master Clues
    ({"Type": "Pvm", "Skill": "Clue_master", "Xp": 2000}, True),  # 2,000 Master Clues
    ({"Type": "Pvm", "Skill": "Clue_master", "Xp": 999}, False),  # Not 1,000 Master Clues
    ({"Type": "Pvm", "Skill": "Collections", "Xp": 100}, True),  # 100 Collections
    ({"Type": "Pvm", "Skill": "Collections", "Xp": 200}, True),  # 200 Collections
    ({"Type": "Pvm", "Skill": "Collections", "Xp": 99}, False),  # Not 100 Collections
    ({"Type": "Skill", "Skill": "Attack", "Xp": 100000000}, False),  # Not notable
    ({"Type": "Skill", "Skill": "Attack", "Xp": 100000000}, False),  # Not notable
])
def test_is_notable(achievement, expected):
    assert is_notable(achievement) == expected