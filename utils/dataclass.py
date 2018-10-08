from dataclasses import dataclass
from dataclasses import fields
from math import sqrt


def from_dict(cls: dataclass, dictionary: dict):
    """Make dataclass object from a dictionary.

    :param cls: The dataclass to make a object of.
    :param dictionary: The dictionary.
    :return: The dataclass object.
    """
    init_kwargs = {}
    for _field in fields(cls):
        field_value = dictionary.get(_field.name)
        init_kwargs[_field.name] = field_value
    return cls(**init_kwargs)


@dataclass
class Attacker:
    alliance_id: int
    character_id: int
    corporation_id: int
    damage_done: int
    faction_id: int
    final_blow: bool
    security_status: float
    ship_type_id: int
    weapon_type_id: int


@dataclass
class Victim:
    alliance_id: int
    character_id: int
    corporation_id: int
    damage_taken: int
    faction_id: int
    items: list
    position: dict
    ship_type_id: int

    def __post_init__(self):
        self.items = [from_dict(cls=Item, dictionary=item) for item in self.items]


@dataclass
class Killmail:
    attackers: list
    killmail_id: int
    killmail_time: str
    moon_id: int
    solar_system_id: int
    victim: Victim or dict
    war_id: int

    def __post_init__(self):
        self.attackers = [from_dict(cls=Attacker, dictionary=attacker) for attacker in self.attackers]
        self.victim = from_dict(cls=Victim, dictionary=self.victim)


@dataclass
class Item:
    flag: int
    item_type_id: int
    quantity_destroyed: int
    quantity_dropped: int
    singleton: int


@dataclass
class Zkb:
    locationID: int
    hash: str
    fittedValue: int
    totalValue: int
    points: int
    npc: bool
    solo: bool
    awox: bool
    href: str


@dataclass
class Config:
    guilds: list

    def __post_init__(self):
        self.guilds = [from_dict(cls=Guild, dictionary=guild) for guild in self.guilds]


@dataclass
class Guild:
    id: int
    channel: int
    staging: dict
    lists: dict
    filters: list
    reported_killmail_id: dict
    active_systems: dict
    ignored_systems: dict

    def __post_init__(self):
        self.filters = [from_dict(cls=Filter, dictionary=filt) for filt in self.filters]


@dataclass
class Filter:
    name: str
    action: str
    what: str
    where: str
    who: str
    who_ignore: str
    range: int
    ping: bool
    isk_value: int
    items: str


@dataclass
class Position:
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def __abs__(self):
        return sqrt((self.x ** 2) + (self.y ** 2) + (self.z ** 2))

    def distance_in_light_years(self, other):
        light_year = 9.4607 * 10 ** 15
        return abs(self - other) / light_year
