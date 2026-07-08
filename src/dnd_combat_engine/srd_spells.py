"""Built-in SRD spell coverage for characters level 10 and under."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from dnd_combat_engine.models.rules import RuleSource
from dnd_combat_engine.models.schema import CURRENT_SCHEMA_VERSION, SCHEMA_VERSION_FIELD

MAX_SUPPORTED_CHARACTER_LEVEL = 10
MAX_SUPPORTED_SPELL_LEVEL = 5

# A level 10 full caster can cast cantrips and spell levels 1 through 5.  This
# table intentionally stores compact metadata and derives common action effects
# below so the engine can load every SRD spell without maintaining hundreds of
# near-identical JSON files.
_SRD_SPELL_ROWS: tuple[tuple[str, str, int, str], ...] = (
    ("acid_splash", "Acid Splash", 0, "conjuration"),
    ("chill_touch", "Chill Touch", 0, "necromancy"),
    ("dancing_lights", "Dancing Lights", 0, "evocation"),
    ("druidcraft", "Druidcraft", 0, "transmutation"),
    ("eldritch_blast", "Eldritch Blast", 0, "evocation"),
    ("fire_bolt", "Fire Bolt", 0, "evocation"),
    ("guidance", "Guidance", 0, "divination"),
    ("light", "Light", 0, "evocation"),
    ("mage_hand", "Mage Hand", 0, "conjuration"),
    ("mending", "Mending", 0, "transmutation"),
    ("message", "Message", 0, "transmutation"),
    ("minor_illusion", "Minor Illusion", 0, "illusion"),
    ("poison_spray", "Poison Spray", 0, "conjuration"),
    ("prestidigitation", "Prestidigitation", 0, "transmutation"),
    ("produce_flame", "Produce Flame", 0, "conjuration"),
    ("ray_of_frost", "Ray of Frost", 0, "evocation"),
    ("resistance", "Resistance", 0, "abjuration"),
    ("sacred_flame", "Sacred Flame", 0, "evocation"),
    ("shillelagh", "Shillelagh", 0, "transmutation"),
    ("shocking_grasp", "Shocking Grasp", 0, "evocation"),
    ("spare_the_dying", "Spare the Dying", 0, "necromancy"),
    ("thaumaturgy", "Thaumaturgy", 0, "transmutation"),
    ("true_strike", "True Strike", 0, "divination"),
    ("vicious_mockery", "Vicious Mockery", 0, "enchantment"),
    ("alarm", "Alarm", 1, "abjuration"),
    ("animal_friendship", "Animal Friendship", 1, "enchantment"),
    ("bane", "Bane", 1, "enchantment"),
    ("bless", "Bless", 1, "enchantment"),
    ("burning_hands", "Burning Hands", 1, "evocation"),
    ("charm_person", "Charm Person", 1, "enchantment"),
    ("color_spray", "Color Spray", 1, "illusion"),
    ("command", "Command", 1, "enchantment"),
    ("compelled_duel", "Compelled Duel", 1, "enchantment"),
    ("comprehend_languages", "Comprehend Languages", 1, "divination"),
    ("create_or_destroy_water", "Create or Destroy Water", 1, "transmutation"),
    ("cure_wounds", "Cure Wounds", 1, "evocation"),
    ("detect_evil_and_good", "Detect Evil and Good", 1, "divination"),
    ("detect_magic", "Detect Magic", 1, "divination"),
    ("detect_poison_and_disease", "Detect Poison and Disease", 1, "divination"),
    ("disguise_self", "Disguise Self", 1, "illusion"),
    ("ensnaring_strike", "Ensnaring Strike", 1, "conjuration"),
    ("entangle", "Entangle", 1, "conjuration"),
    ("expeditious_retreat", "Expeditious Retreat", 1, "transmutation"),
    ("faerie_fire", "Faerie Fire", 1, "evocation"),
    ("false_life", "False Life", 1, "necromancy"),
    ("feather_fall", "Feather Fall", 1, "transmutation"),
    ("floating_disk", "Floating Disk", 1, "conjuration"),
    ("fog_cloud", "Fog Cloud", 1, "conjuration"),
    ("goodberry", "Goodberry", 1, "transmutation"),
    ("grease", "Grease", 1, "conjuration"),
    ("guiding_bolt", "Guiding Bolt", 1, "evocation"),
    ("hail_of_thorns", "Hail of Thorns", 1, "conjuration"),
    ("healing_word", "Healing Word", 1, "evocation"),
    ("hellish_rebuke", "Hellish Rebuke", 1, "evocation"),
    ("heroism", "Heroism", 1, "enchantment"),
    ("hideous_laughter", "Hideous Laughter", 1, "enchantment"),
    ("hunters_mark", "Hunter's Mark", 1, "divination"),
    ("identify", "Identify", 1, "divination"),
    ("illusory_script", "Illusory Script", 1, "illusion"),
    ("inflict_wounds", "Inflict Wounds", 1, "necromancy"),
    ("jump", "Jump", 1, "transmutation"),
    ("longstrider", "Longstrider", 1, "transmutation"),
    ("mage_armor", "Mage Armor", 1, "abjuration"),
    ("magic_missile", "Magic Missile", 1, "evocation"),
    ("protection_from_evil_and_good", "Protection from Evil and Good", 1, "abjuration"),
    ("purify_food_and_drink", "Purify Food and Drink", 1, "transmutation"),
    ("sanctuary", "Sanctuary", 1, "abjuration"),
    ("searing_smite", "Searing Smite", 1, "evocation"),
    ("shield", "Shield", 1, "abjuration"),
    ("shield_of_faith", "Shield of Faith", 1, "abjuration"),
    ("silent_image", "Silent Image", 1, "illusion"),
    ("sleep", "Sleep", 1, "enchantment"),
    ("speak_with_animals", "Speak with Animals", 1, "divination"),
    ("thunderous_smite", "Thunderous Smite", 1, "evocation"),
    ("thunderwave", "Thunderwave", 1, "evocation"),
    ("unseen_servant", "Unseen Servant", 1, "conjuration"),
    ("witch_bolt", "Witch Bolt", 1, "evocation"),
    ("wrathful_smite", "Wrathful Smite", 1, "evocation"),
    ("aid", "Aid", 2, "abjuration"),
    ("alter_self", "Alter Self", 2, "transmutation"),
    ("animal_messenger", "Animal Messenger", 2, "enchantment"),
    ("arcane_lock", "Arcane Lock", 2, "abjuration"),
    ("arcanists_magic_aura", "Arcanist's Magic Aura", 2, "illusion"),
    ("augury", "Augury", 2, "divination"),
    ("barkskin", "Barkskin", 2, "transmutation"),
    ("beast_sense", "Beast Sense", 2, "divination"),
    ("blindness_deafness", "Blindness/Deafness", 2, "necromancy"),
    ("blur", "Blur", 2, "illusion"),
    ("branding_smite", "Branding Smite", 2, "evocation"),
    ("calm_emotions", "Calm Emotions", 2, "enchantment"),
    ("continual_flame", "Continual Flame", 2, "evocation"),
    ("cordon_of_arrows", "Cordon of Arrows", 2, "transmutation"),
    ("darkness", "Darkness", 2, "evocation"),
    ("darkvision", "Darkvision", 2, "transmutation"),
    ("detect_thoughts", "Detect Thoughts", 2, "divination"),
    ("enhance_ability", "Enhance Ability", 2, "transmutation"),
    ("enlarge_reduce", "Enlarge/Reduce", 2, "transmutation"),
    ("find_steed", "Find Steed", 2, "conjuration"),
    ("find_traps", "Find Traps", 2, "divination"),
    ("flame_blade", "Flame Blade", 2, "evocation"),
    ("flaming_sphere", "Flaming Sphere", 2, "conjuration"),
    ("gentle_repose", "Gentle Repose", 2, "necromancy"),
    ("gust_of_wind", "Gust of Wind", 2, "evocation"),
    ("heat_metal", "Heat Metal", 2, "transmutation"),
    ("hold_person", "Hold Person", 2, "enchantment"),
    ("invisibility", "Invisibility", 2, "illusion"),
    ("knock", "Knock", 2, "transmutation"),
    ("lesser_restoration", "Lesser Restoration", 2, "abjuration"),
    ("levitate", "Levitate", 2, "transmutation"),
    ("locate_animals_or_plants", "Locate Animals or Plants", 2, "divination"),
    ("locate_object", "Locate Object", 2, "divination"),
    ("magic_mouth", "Magic Mouth", 2, "illusion"),
    ("magic_weapon", "Magic Weapon", 2, "transmutation"),
    ("mirror_image", "Mirror Image", 2, "illusion"),
    ("misty_step", "Misty Step", 2, "conjuration"),
    ("moonbeam", "Moonbeam", 2, "evocation"),
    ("pass_without_trace", "Pass without Trace", 2, "abjuration"),
    ("phantasmal_force", "Phantasmal Force", 2, "illusion"),
    ("prayer_of_healing", "Prayer of Healing", 2, "evocation"),
    ("protection_from_poison", "Protection from Poison", 2, "abjuration"),
    ("ray_of_enfeeblement", "Ray of Enfeeblement", 2, "necromancy"),
    ("rope_trick", "Rope Trick", 2, "transmutation"),
    ("scorching_ray", "Scorching Ray", 2, "evocation"),
    ("see_invisibility", "See Invisibility", 2, "divination"),
    ("shatter", "Shatter", 2, "evocation"),
    ("silence", "Silence", 2, "illusion"),
    ("spider_climb", "Spider Climb", 2, "transmutation"),
    ("spike_growth", "Spike Growth", 2, "transmutation"),
    ("spiritual_weapon", "Spiritual Weapon", 2, "evocation"),
    ("suggestion", "Suggestion", 2, "enchantment"),
    ("warding_bond", "Warding Bond", 2, "abjuration"),
    ("web", "Web", 2, "conjuration"),
    ("zone_of_truth", "Zone of Truth", 2, "enchantment"),
    ("animate_dead", "Animate Dead", 3, "necromancy"),
    ("beacon_of_hope", "Beacon of Hope", 3, "abjuration"),
    ("bestow_curse", "Bestow Curse", 3, "necromancy"),
    ("blinding_smite", "Blinding Smite", 3, "evocation"),
    ("call_lightning", "Call Lightning", 3, "conjuration"),
    ("clairvoyance", "Clairvoyance", 3, "divination"),
    ("conjure_animals", "Conjure Animals", 3, "conjuration"),
    ("conjure_barrage", "Conjure Barrage", 3, "conjuration"),
    ("counterspell", "Counterspell", 3, "abjuration"),
    ("create_food_and_water", "Create Food and Water", 3, "conjuration"),
    ("crusaders_mantle", "Crusader's Mantle", 3, "evocation"),
    ("daylight", "Daylight", 3, "evocation"),
    ("dispel_magic", "Dispel Magic", 3, "abjuration"),
    ("elemental_weapon", "Elemental Weapon", 3, "transmutation"),
    ("fear", "Fear", 3, "illusion"),
    ("fireball", "Fireball", 3, "evocation"),
    ("fly", "Fly", 3, "transmutation"),
    ("gaseous_form", "Gaseous Form", 3, "transmutation"),
    ("glyph_of_warding", "Glyph of Warding", 3, "abjuration"),
    ("haste", "Haste", 3, "transmutation"),
    ("hypnotic_pattern", "Hypnotic Pattern", 3, "illusion"),
    ("lightning_arrow", "Lightning Arrow", 3, "transmutation"),
    ("lightning_bolt", "Lightning Bolt", 3, "evocation"),
    ("magic_circle", "Magic Circle", 3, "abjuration"),
    ("major_image", "Major Image", 3, "illusion"),
    ("mass_healing_word", "Mass Healing Word", 3, "evocation"),
    ("meld_into_stone", "Meld into Stone", 3, "transmutation"),
    ("nondetection", "Nondetection", 3, "abjuration"),
    ("phantom_steed", "Phantom Steed", 3, "illusion"),
    ("plant_growth", "Plant Growth", 3, "transmutation"),
    ("protection_from_energy", "Protection from Energy", 3, "abjuration"),
    ("remove_curse", "Remove Curse", 3, "abjuration"),
    ("revivify", "Revivify", 3, "necromancy"),
    ("sending", "Sending", 3, "evocation"),
    ("sleet_storm", "Sleet Storm", 3, "conjuration"),
    ("slow", "Slow", 3, "transmutation"),
    ("speak_with_dead", "Speak with Dead", 3, "necromancy"),
    ("speak_with_plants", "Speak with Plants", 3, "transmutation"),
    ("spirit_guardians", "Spirit Guardians", 3, "conjuration"),
    ("stinking_cloud", "Stinking Cloud", 3, "conjuration"),
    ("tongues", "Tongues", 3, "divination"),
    ("vampiric_touch", "Vampiric Touch", 3, "necromancy"),
    ("water_breathing", "Water Breathing", 3, "transmutation"),
    ("water_walk", "Water Walk", 3, "transmutation"),
    ("wind_wall", "Wind Wall", 3, "evocation"),
    ("arcane_eye", "Arcane Eye", 4, "divination"),
    ("banishment", "Banishment", 4, "abjuration"),
    ("black_tentacles", "Black Tentacles", 4, "conjuration"),
    ("blight", "Blight", 4, "necromancy"),
    ("compulsion", "Compulsion", 4, "enchantment"),
    ("confusion", "Confusion", 4, "enchantment"),
    ("conjure_minor_elementals", "Conjure Minor Elementals", 4, "conjuration"),
    ("conjure_woodland_beings", "Conjure Woodland Beings", 4, "conjuration"),
    ("control_water", "Control Water", 4, "transmutation"),
    ("death_ward", "Death Ward", 4, "abjuration"),
    ("dimension_door", "Dimension Door", 4, "conjuration"),
    ("divination", "Divination", 4, "divination"),
    ("dominate_beast", "Dominate Beast", 4, "enchantment"),
    ("faithful_hound", "Faithful Hound", 4, "conjuration"),
    ("fire_shield", "Fire Shield", 4, "evocation"),
    ("freedom_of_movement", "Freedom of Movement", 4, "abjuration"),
    ("giant_insect", "Giant Insect", 4, "transmutation"),
    ("grasping_vine", "Grasping Vine", 4, "conjuration"),
    ("greater_invisibility", "Greater Invisibility", 4, "illusion"),
    ("guardian_of_faith", "Guardian of Faith", 4, "conjuration"),
    ("hallucinatory_terrain", "Hallucinatory Terrain", 4, "illusion"),
    ("ice_storm", "Ice Storm", 4, "evocation"),
    ("locate_creature", "Locate Creature", 4, "divination"),
    ("phantasmal_killer", "Phantasmal Killer", 4, "illusion"),
    ("polymorph", "Polymorph", 4, "transmutation"),
    ("private_sanctum", "Private Sanctum", 4, "abjuration"),
    ("resilient_sphere", "Resilient Sphere", 4, "evocation"),
    ("secret_chest", "Secret Chest", 4, "conjuration"),
    ("staggering_smite", "Staggering Smite", 4, "evocation"),
    ("stone_shape", "Stone Shape", 4, "transmutation"),
    ("stoneskin", "Stoneskin", 4, "abjuration"),
    ("wall_of_fire", "Wall of Fire", 4, "evocation"),
    ("animate_objects", "Animate Objects", 5, "transmutation"),
    ("antilife_shell", "Antilife Shell", 5, "abjuration"),
    ("awaken", "Awaken", 5, "transmutation"),
    ("banishing_smite", "Banishing Smite", 5, "abjuration"),
    ("circle_of_power", "Circle of Power", 5, "abjuration"),
    ("cloudkill", "Cloudkill", 5, "conjuration"),
    ("commune", "Commune", 5, "divination"),
    ("commune_with_nature", "Commune with Nature", 5, "divination"),
    ("cone_of_cold", "Cone of Cold", 5, "evocation"),
    ("conjure_elemental", "Conjure Elemental", 5, "conjuration"),
    ("conjure_volley", "Conjure Volley", 5, "conjuration"),
    ("contact_other_plane", "Contact Other Plane", 5, "divination"),
    ("contagion", "Contagion", 5, "necromancy"),
    ("creation", "Creation", 5, "illusion"),
    ("destructive_wave", "Destructive Wave", 5, "evocation"),
    ("dispel_evil_and_good", "Dispel Evil and Good", 5, "abjuration"),
    ("dominate_person", "Dominate Person", 5, "enchantment"),
    ("dream", "Dream", 5, "illusion"),
    ("flame_strike", "Flame Strike", 5, "evocation"),
    ("geas", "Geas", 5, "enchantment"),
    ("greater_restoration", "Greater Restoration", 5, "abjuration"),
    ("hallow", "Hallow", 5, "evocation"),
    ("hold_monster", "Hold Monster", 5, "enchantment"),
    ("insect_plague", "Insect Plague", 5, "conjuration"),
    ("legend_lore", "Legend Lore", 5, "divination"),
    ("mass_cure_wounds", "Mass Cure Wounds", 5, "evocation"),
    ("mislead", "Mislead", 5, "illusion"),
    ("modify_memory", "Modify Memory", 5, "enchantment"),
    ("passwall", "Passwall", 5, "transmutation"),
    ("planar_binding", "Planar Binding", 5, "abjuration"),
    ("raise_dead", "Raise Dead", 5, "necromancy"),
    ("reincarnate", "Reincarnate", 5, "transmutation"),
    ("scrying", "Scrying", 5, "divination"),
    ("seeming", "Seeming", 5, "illusion"),
    ("swift_quiver", "Swift Quiver", 5, "transmutation"),
    ("telekinesis", "Telekinesis", 5, "transmutation"),
    ("telepathic_bond", "Telepathic Bond", 5, "divination"),
    ("tree_stride", "Tree Stride", 5, "conjuration"),
    ("wall_of_force", "Wall of Force", 5, "evocation"),
    ("wall_of_stone", "Wall of Stone", 5, "evocation"),
)

_SRD_SPELL_INDEX = {spell_id: row for spell_id, *row in _SRD_SPELL_ROWS}

_CONCENTRATION_IDS = frozenset(
    {
        "bane",
        "bless",
        "compelled_duel",
        "dancing_lights",
        "detect_evil_and_good",
        "detect_magic",
        "detect_poison_and_disease",
        "ensnaring_strike",
        "entangle",
        "expeditious_retreat",
        "faerie_fire",
        "fog_cloud",
        "guidance",
        "hail_of_thorns",
        "heroism",
        "hideous_laughter",
        "hunters_mark",
        "protection_from_evil_and_good",
        "resistance",
        "searing_smite",
        "shield_of_faith",
        "silent_image",
        "thunderous_smite",
        "true_strike",
        "witch_bolt",
        "wrathful_smite",
        "alter_self",
        "barkskin",
        "beast_sense",
        "blur",
        "branding_smite",
        "calm_emotions",
        "detect_thoughts",
        "enhance_ability",
        "enlarge_reduce",
        "flame_blade",
        "flaming_sphere",
        "gust_of_wind",
        "heat_metal",
        "hold_person",
        "invisibility",
        "levitate",
        "locate_object",
        "magic_weapon",
        "moonbeam",
        "pass_without_trace",
        "phantasmal_force",
        "ray_of_enfeeblement",
        "silence",
        "spider_climb",
        "spike_growth",
        "suggestion",
        "web",
        "beacon_of_hope",
        "bestow_curse",
        "blinding_smite",
        "call_lightning",
        "clairvoyance",
        "conjure_animals",
        "crusaders_mantle",
        "elemental_weapon",
        "fear",
        "fly",
        "gaseous_form",
        "haste",
        "hypnotic_pattern",
        "lightning_arrow",
        "major_image",
        "nondetection",
        "protection_from_energy",
        "sleet_storm",
        "slow",
        "spirit_guardians",
        "stinking_cloud",
        "vampiric_touch",
        "wind_wall",
        "arcane_eye",
        "banishment",
        "black_tentacles",
        "compulsion",
        "confusion",
        "conjure_minor_elementals",
        "conjure_woodland_beings",
        "control_water",
        "dominate_beast",
        "giant_insect",
        "grasping_vine",
        "greater_invisibility",
        "phantasmal_killer",
        "polymorph",
        "resilient_sphere",
        "staggering_smite",
        "stoneskin",
        "wall_of_fire",
        "animate_objects",
        "antilife_shell",
        "banishing_smite",
        "circle_of_power",
        "cloudkill",
        "conjure_elemental",
        "dispel_evil_and_good",
        "dominate_person",
        "hold_monster",
        "insect_plague",
        "mislead",
        "modify_memory",
        "scrying",
        "swift_quiver",
        "telekinesis",
        "tree_stride",
        "wall_of_force",
        "wall_of_stone",
    }
)

_RITUAL_IDS = frozenset(
    {
        "alarm",
        "animal_messenger",
        "augury",
        "commune",
        "commune_with_nature",
        "comprehend_languages",
        "contact_other_plane",
        "detect_magic",
        "detect_poison_and_disease",
        "divination",
        "find_steed",
        "floating_disk",
        "gentle_repose",
        "identify",
        "illusory_script",
        "locate_animals_or_plants",
        "magic_mouth",
        "meld_into_stone",
        "phantom_steed",
        "purify_food_and_drink",
        "silence",
        "speak_with_animals",
        "telepathic_bond",
        "unseen_servant",
        "water_breathing",
        "water_walk",
    }
)

_DAMAGE: dict[str, tuple[str, str]] = {
    "acid_splash": ("1d6", "acid"),
    "chill_touch": ("1d8", "necrotic"),
    "eldritch_blast": ("1d10", "force"),
    "fire_bolt": ("1d10", "fire"),
    "poison_spray": ("1d12", "poison"),
    "produce_flame": ("1d8", "fire"),
    "ray_of_frost": ("1d8", "cold"),
    "sacred_flame": ("1d8", "radiant"),
    "shocking_grasp": ("1d8", "lightning"),
    "vicious_mockery": ("1d4", "psychic"),
    "burning_hands": ("3d6", "fire"),
    "guiding_bolt": ("4d6", "radiant"),
    "hellish_rebuke": ("2d10", "fire"),
    "inflict_wounds": ("3d10", "necrotic"),
    "magic_missile": ("3d4+3", "force"),
    "thunderwave": ("2d8", "thunder"),
    "witch_bolt": ("1d12", "lightning"),
    "flame_blade": ("3d6", "fire"),
    "flaming_sphere": ("2d6", "fire"),
    "heat_metal": ("2d8", "fire"),
    "moonbeam": ("2d10", "radiant"),
    "scorching_ray": ("6d6", "fire"),
    "shatter": ("3d8", "thunder"),
    "spike_growth": ("2d4", "piercing"),
    "blinding_smite": ("3d8", "radiant"),
    "call_lightning": ("3d10", "lightning"),
    "conjure_barrage": ("3d8", "slashing"),
    "fireball": ("8d6", "fire"),
    "lightning_arrow": ("4d8", "lightning"),
    "lightning_bolt": ("8d6", "lightning"),
    "spirit_guardians": ("3d8", "radiant"),
    "vampiric_touch": ("3d6", "necrotic"),
    "black_tentacles": ("3d6", "bludgeoning"),
    "blight": ("8d8", "necrotic"),
    "fire_shield": ("2d8", "fire"),
    "guardian_of_faith": ("60", "radiant"),
    "ice_storm": ("2d8+4d6", "cold"),
    "phantasmal_killer": ("4d10", "psychic"),
    "staggering_smite": ("4d6", "psychic"),
    "wall_of_fire": ("5d8", "fire"),
    "banishing_smite": ("5d10", "force"),
    "cloudkill": ("5d8", "poison"),
    "cone_of_cold": ("8d8", "cold"),
    "conjure_volley": ("8d8", "piercing"),
    "destructive_wave": ("10d6", "thunder"),
    "flame_strike": ("8d6", "fire"),
    "insect_plague": ("4d10", "piercing"),
}

_DICE_ONLY: dict[str, str] = {
    "bane": "1d4",
    "bless": "1d4",
    "color_spray": "6d10",
    "false_life": "1d4+4",
    "guidance": "1d4",
    "healing_word": "1d4+spellcasting_modifier",
    "resistance": "1d4",
    "sleep": "5d8",
    "cure_wounds": "1d8+spellcasting_modifier",
    "prayer_of_healing": "2d8+spellcasting_modifier",
    "mass_healing_word": "1d4+spellcasting_modifier",
    "mass_cure_wounds": "3d8+spellcasting_modifier",
}

_SAVING_THROWS = {
    "acid_splash": "dexterity",
    "animal_friendship": "wisdom",
    "bane": "charisma",
    "burning_hands": "dexterity",
    "charm_person": "wisdom",
    "command": "wisdom",
    "compelled_duel": "wisdom",
    "ensnaring_strike": "strength",
    "entangle": "strength",
    "faerie_fire": "dexterity",
    "grease": "dexterity",
    "hellish_rebuke": "dexterity",
    "hideous_laughter": "wisdom",
    "poison_spray": "constitution",
    "sacred_flame": "dexterity",
    "thunderous_smite": "strength",
    "thunderwave": "constitution",
    "vicious_mockery": "wisdom",
    "wrathful_smite": "wisdom",
    "blindness_deafness": "constitution",
    "calm_emotions": "charisma",
    "detect_thoughts": "wisdom",
    "enlarge_reduce": "constitution",
    "flaming_sphere": "dexterity",
    "gust_of_wind": "strength",
    "hold_person": "wisdom",
    "levitate": "constitution",
    "moonbeam": "constitution",
    "phantasmal_force": "intelligence",
    "shatter": "constitution",
    "web": "dexterity",
    "zone_of_truth": "charisma",
    "bestow_curse": "wisdom",
    "blinding_smite": "constitution",
    "call_lightning": "dexterity",
    "conjure_barrage": "dexterity",
    "fear": "wisdom",
    "fireball": "dexterity",
    "glyph_of_warding": "dexterity",
    "hypnotic_pattern": "wisdom",
    "lightning_arrow": "dexterity",
    "lightning_bolt": "dexterity",
    "sleet_storm": "dexterity",
    "slow": "wisdom",
    "spirit_guardians": "wisdom",
    "stinking_cloud": "constitution",
    "banishment": "charisma",
    "black_tentacles": "dexterity",
    "blight": "constitution",
    "compulsion": "wisdom",
    "confusion": "wisdom",
    "control_water": "strength",
    "dominate_beast": "wisdom",
    "grasping_vine": "dexterity",
    "ice_storm": "dexterity",
    "phantasmal_killer": "wisdom",
    "polymorph": "wisdom",
    "resilient_sphere": "dexterity",
    "wall_of_fire": "dexterity",
    "cloudkill": "constitution",
    "cone_of_cold": "constitution",
    "conjure_volley": "dexterity",
    "contagion": "constitution",
    "destructive_wave": "constitution",
    "dispel_evil_and_good": "charisma",
    "dominate_person": "wisdom",
    "flame_strike": "dexterity",
    "hold_monster": "wisdom",
    "insect_plague": "constitution",
    "modify_memory": "wisdom",
    "telekinesis": "strength",
    "wall_of_stone": "dexterity",
}

_BONUS_ACTION_IDS = frozenset(
    {
        "ensnaring_strike",
        "expeditious_retreat",
        "hail_of_thorns",
        "healing_word",
        "hunters_mark",
        "misty_step",
        "sanctuary",
        "searing_smite",
        "shillelagh",
        "shield_of_faith",
        "spiritual_weapon",
        "thunderous_smite",
        "wrathful_smite",
        "blinding_smite",
        "lightning_arrow",
        "staggering_smite",
        "grasping_vine",
        "banishing_smite",
        "swift_quiver",
    }
)
_REACTION_IDS = frozenset({"counterspell", "feather_fall", "hellish_rebuke", "shield"})
_SELF_IDS = frozenset(
    {
        "alter_self",
        "arcane_eye",
        "beast_sense",
        "blur",
        "commune",
        "commune_with_nature",
        "comprehend_languages",
        "detect_evil_and_good",
        "detect_magic",
        "detect_poison_and_disease",
        "disguise_self",
        "expeditious_retreat",
        "false_life",
        "fire_shield",
        "gaseous_form",
        "mislead",
        "produce_flame",
        "see_invisibility",
        "speak_with_animals",
        "spider_climb",
        "tree_stride",
    }
)
_AREA_IDS = frozenset(
    {
        "alarm",
        "cloudkill",
        "conjure_barrage",
        "conjure_volley",
        "control_water",
        "darkness",
        "daylight",
        "entangle",
        "faerie_fire",
        "fireball",
        "fog_cloud",
        "grease",
        "hypnotic_pattern",
        "ice_storm",
        "insect_plague",
        "moonbeam",
        "plant_growth",
        "sleet_storm",
        "sleep",
        "spike_growth",
        "spirit_guardians",
        "stinking_cloud",
        "wall_of_fire",
        "wall_of_force",
        "wall_of_stone",
        "web",
        "wind_wall",
    }
)
_MULTIPLE_TARGET_IDS = frozenset(
    {
        "aid",
        "bane",
        "bless",
        "color_spray",
        "create_food_and_water",
        "crusaders_mantle",
        "destructive_wave",
        "feather_fall",
        "mass_cure_wounds",
        "mass_healing_word",
        "prayer_of_healing",
        "seeming",
        "slow",
        "telepathic_bond",
        "water_breathing",
        "water_walk",
    }
)
_HEALING_IDS = frozenset(
    {
        "cure_wounds",
        "goodberry",
        "greater_restoration",
        "healing_word",
        "mass_cure_wounds",
        "mass_healing_word",
        "prayer_of_healing",
        "raise_dead",
        "reincarnate",
        "revivify",
        "spare_the_dying",
    }
)
_CONDITION_IDS = frozenset(
    {
        "animal_friendship",
        "bane",
        "banishment",
        "bestow_curse",
        "blindness_deafness",
        "calm_emotions",
        "charm_person",
        "command",
        "compelled_duel",
        "confusion",
        "contagion",
        "dominate_beast",
        "dominate_person",
        "ensnaring_strike",
        "entangle",
        "faerie_fire",
        "fear",
        "geas",
        "hold_monster",
        "hold_person",
        "hypnotic_pattern",
        "modify_memory",
        "phantasmal_killer",
        "polymorph",
        "sleep",
        "slow",
        "suggestion",
        "web",
        "zone_of_truth",
    }
)


def list_srd_spell_ids(max_spell_level: int = MAX_SUPPORTED_SPELL_LEVEL) -> list[str]:
    """List built-in SRD spell ids up to the requested spell level."""
    return sorted(
        spell_id for spell_id, _, level, _ in _SRD_SPELL_ROWS if level <= max_spell_level
    )


def get_srd_spell_data(spell_id: str) -> dict[str, Any] | None:
    """Return JSON-compatible built-in SRD spell data, if available."""
    row = _SRD_SPELL_INDEX.get(spell_id)
    if row is None:
        return None
    name, level, school = row
    return deepcopy(_spell_data(spell_id, name, level, school))


def srd_spell_level_counts(max_spell_level: int = MAX_SUPPORTED_SPELL_LEVEL) -> dict[int, int]:
    """Return the number of built-in SRD spells by spell level."""
    counts = {level: 0 for level in range(max_spell_level + 1)}
    for _, _, level, _ in _SRD_SPELL_ROWS:
        if level <= max_spell_level:
            counts[level] += 1
    return counts


def _spell_data(spell_id: str, name: str, level: int, school: str) -> dict[str, Any]:
    dice = _effect_dice(spell_id)
    effect_kind = _effect_kind(spell_id)
    rule_source = RuleSource.srd_5_2_1(f"Spells: {name}").to_dict()
    data: dict[str, Any] = {
        SCHEMA_VERSION_FIELD: CURRENT_SCHEMA_VERSION,
        "spell_id": spell_id,
        "name": name,
        "level": level,
        "school": school,
        "casting_time": _casting_time(spell_id),
        "range_text": _range_text(spell_id),
        "duration": _duration_text(spell_id),
        "components": ["V", "S"],
        "concentration": spell_id in _CONCENTRATION_IDS,
        "ritual": spell_id in _RITUAL_IDS,
        "damage": _damage_profile(spell_id),
        "saving_throw": _SAVING_THROWS.get(spell_id),
        "effects": [
            {
                "effect_id": f"{spell_id}-{effect_kind}",
                "name": name,
                "effect_kind": effect_kind,
                "target_profile": _target_profile(spell_id),
                "action_cost": _action_cost(spell_id),
                "duration": _duration_profile(spell_id),
                "check": _check_definition(spell_id),
                "resource_cost": None if level == 0 else f"spell_slot_{level}",
                "dice": dice,
                "rule_source": rule_source,
            }
        ],
        "description": (
            f"SRD 5.2.1 spell metadata for {name}. Detailed spell text is not "
            "bundled; this entry provides compendium and action-bar support."
        ),
        "rule_source": rule_source,
    }
    return data


def _effect_kind(spell_id: str) -> str:
    if spell_id in _DAMAGE:
        return "damage"
    if spell_id in _HEALING_IDS:
        return "healing"
    if spell_id in _CONDITION_IDS:
        return "condition"
    if spell_id in _CONCENTRATION_IDS:
        return "buff"
    return "utility"


def _effect_dice(spell_id: str) -> str | None:
    if spell_id in _DAMAGE:
        return _DAMAGE[spell_id][0]
    return _DICE_ONLY.get(spell_id)


def _damage_profile(spell_id: str) -> list[dict[str, str]] | None:
    damage = _DAMAGE.get(spell_id)
    if damage is None:
        return None
    dice, damage_type = damage
    return [{"dice": dice, "damage_type": damage_type}]


def _target_profile(spell_id: str) -> str:
    if spell_id in _SELF_IDS:
        return "self"
    if spell_id in _AREA_IDS:
        return "area"
    if spell_id in _MULTIPLE_TARGET_IDS:
        return "multiple_creatures"
    if spell_id in {"druidcraft", "prestidigitation", "thaumaturgy"}:
        return "special"
    if spell_id in {"mending", "light", "arcane_lock", "magic_mouth"}:
        return "object"
    return "one_creature"


def _action_cost(spell_id: str) -> str:
    if spell_id in _BONUS_ACTION_IDS:
        return "bonus_action"
    if spell_id in _REACTION_IDS:
        return "reaction"
    return "action"


def _casting_time(spell_id: str) -> str:
    if spell_id in _BONUS_ACTION_IDS:
        return "1 bonus action"
    if spell_id in _REACTION_IDS:
        return "1 reaction"
    if spell_id in _RITUAL_IDS:
        return "1 action or ritual"
    return "1 action"


def _range_text(spell_id: str) -> str:
    if spell_id in _SELF_IDS:
        return "Self"
    if spell_id in {"cure_wounds", "light", "mending", "spare_the_dying"}:
        return "Touch"
    if spell_id in _AREA_IDS:
        return "Area"
    return "SRD range"


def _duration_text(spell_id: str) -> str:
    if spell_id in _CONCENTRATION_IDS:
        return "Concentration, SRD duration"
    return "SRD duration"


def _duration_profile(spell_id: str) -> dict[str, Any]:
    if spell_id in _CONCENTRATION_IDS:
        return {"kind": "concentration", "amount": None, "text": _duration_text(spell_id)}
    return {"kind": "special", "amount": None, "text": _duration_text(spell_id)}


def _check_definition(spell_id: str) -> dict[str, Any]:
    ability = _SAVING_THROWS.get(spell_id)
    return {
        "kind": "saving_throw" if ability else "none",
        "ability": ability,
        "dc": None,
        "bonus": 0,
        "proficiency_applies": False,
    }
