import json


with open("data/CasaAS.json", "r") as f:
    network = json.load(f)


# CODE:


# --- MODEL ---
class NetworkArrow:
    def __init__(self, id, source, target, ownership_share):
        self.id = id
        self.source = source
        self.target = target

        self.direct_ownership_lower = parse_share(ownership_share)[0] / 100
        self.direct_ownership_upper = parse_share(ownership_share)[1] / 100

    def direct_ownership_average(self):
        return (self.direct_ownership_lower + self.direct_ownership_upper) / 2

    def serialize(self):
        return {
            "source": self.source,
            "target": self.target,
            "direct_ownership_lower": self.direct_ownership_lower,
            "direct_ownership_average": self.direct_ownership_average(),
            "direct_ownership_upper": self.direct_ownership_upper,
        }


class NetworkModel:
    id_to_network_arrows_map = dict()
    arrows_into_id_map = dict()
    arrows_out_of_id_map = dict()

    def contains_network_arrow_with_id(self, id):
        return id in self.id_to_network_arrows_map.keys()

    def add_network_relationships(self, network_arrow_descriptor):
        id = network_arrow_descriptor["id"]

        if not self.contains_network_arrow_with_id(id):

            network_arrow_model = NetworkArrow(
                network_arrow_descriptor["id"],
                network_arrow_descriptor["source"],
                network_arrow_descriptor["target"],
                network_arrow_descriptor["share"],
            )

            self.add_network_arrow(network_arrow_model)
            self.add_network_arrow_target_relation(network_arrow_model)
            self.add_network_arrow_source_relation(network_arrow_model)

    def add_network_arrow(self, network_arrow_model):
        self.id_to_network_arrows_map[network_arrow_model.id] = network_arrow_model

    def add_network_arrow_target_relation(self, network_arrow_model):
        target_id = network_arrow_model.target

        if target_id not in self.arrows_into_id_map:
            self.arrows_into_id_map[target_id] = [network_arrow_model]
        else:
            self.arrows_into_id_map[target_id].append(network_arrow_model)

    def add_network_arrow_source_relation(self, ownership):
        identifier = ownership.source

        if identifier not in self.arrows_out_of_id_map:
            self.arrows_out_of_id_map[identifier] = [ownership]
        else:
            self.arrows_out_of_id_map[identifier].append(ownership)

    def get_arrows_into(self, id):
        if id in self.arrows_into_id_map:
            return self.arrows_into_id_map[id]
        return []

    def get_arrows_out_of(self, id):
        if id in self.arrows_out_of_id_map:
            return self.arrows_out_of_id_map[id]
        return []

    def serialize(self):
        return dict(
            [(k, v.serialize()) for k, v in self.id_to_network_arrows_map.items()]
        )


class NetworkPath:
    path = []

    lower_weight = 1
    upper_weight = 1

    def average_weight(self):
        return (self.lower_weight + self.upper_weight) / 2

    def __init__(self, path, lower_weight=1, upper_weight=1):
        self.path = path
        self.lower_weight = lower_weight
        self.upper_weight = upper_weight

    @classmethod
    def start(cls, ownership):
        return cls(
            [ownership.source, ownership.target],
            ownership.direct_ownership_lower,
            ownership.direct_ownership_upper,
        )

    def from_node(self):
        return self.path[0]

    def to_node(self):
        return self.path[-1]

    def append_arrow(self, ownership):
        if self.to_node() != ownership.source:
            print(self.to_node(), ownership.source, self.path)
            raise ValueError("Ownership does not match source company")
        if ownership.target in self.path:
            return None

        new_path = self.path + [ownership.target]

        return NetworkPath(
            new_path,
            self.lower_weight * ownership.direct_ownership_lower,
            self.upper_weight * ownership.direct_ownership_upper,
        )

    def prepend_arrow(self, ownership):
        if self.from_node() != ownership.target:
            raise ValueError("Ownership does not match target company")
        if ownership.source in self.path:
            return None

        new_path = [ownership.source] + self.path
        return NetworkPath(
            new_path,
            self.lower_weight * ownership.direct_ownership_lower,
            self.upper_weight * ownership.direct_ownership_upper,
        )

    def __str__(self):
        return json.dumps(self.serialize())

    def serialize(self):
        return {
            "source": self.from_node(),
            "target": self.to_node(),
            "real_lower_share": self.lower_weight,
            "real_average_share": self.average_weight(),
            "real_upper_share": self.upper_weight,
        }


# --- HELPERS ---
def remove_percentage_sign(string):
    return string.split("%")[0]


# Expected shape of 'share' string is "[\d+]-[\d+]%" OR "[\d+]%" OR "<[\d+]%"
def parse_share(share):
    less_than_split = share.split("<")
    if len(less_than_split) > 1:
        return [0, float(remove_percentage_sign(less_than_split[1]))]

    interval_ends = share.split("-")

    start = float(remove_percentage_sign(interval_ends[0]))
    if len(interval_ends) == 1:
        return [start, start]
    elif len(interval_ends) == 2:
        return [start, float(remove_percentage_sign(interval_ends[1]))]


# --- EXTRACT INTO MODEL ---
network_model = NetworkModel()
focus_company_id = None

# Load companies and direct ownerships
for company_ownership in network:
    # company_map.add_source_and_target(company_ownership)
    network_model.add_network_relationships(company_ownership)

    if company_ownership["source_depth"] == 0 and focus_company_id is None:
        focus_company_id = company_ownership["source"]
    elif company_ownership["target_depth"] == 0 and focus_company_id is None:
        focus_company_id = company_ownership["target"]


# --- TRAVERSE NETWORK ---

# $$ ------ ABOVE FOCUS COMPANY ------ $$
owns = [
    NetworkPath.start(ownership)
    for ownership in network_model.get_arrows_into(focus_company_id)
    if ownership.source != focus_company_id
]


def travel_backwards(newest_paths, all_paths):
    new_paths = []

    for path in newest_paths:
        arrows_mapping_in = network_model.get_arrows_into(path.from_node())
        if len(arrows_mapping_in) != 0:
            for arrow in arrows_mapping_in:
                extended_path = path.prepend_arrow(arrow)
                if extended_path is not None:
                    new_paths.append(extended_path)

    if len(new_paths) == 0:
        return [], all_paths
    else:
        all_paths.extend(new_paths)
        return travel_backwards(new_paths, all_paths)


empty, owned_by_structure = travel_backwards(owns, owns)

with open("output/isOwnedBy.json", "w", encoding="utf-8") as f:
    json.dump(
        [ownership.serialize() for ownership in owned_by_structure],
        f,
        ensure_ascii=False,
        indent=4,
    )


# $$ ------ BELOW FOCUS COMPANY ------ $$

owns = [
    NetworkPath.start(ownership)
    for ownership in network_model.get_arrows_out_of(focus_company_id)
    if ownership.target != focus_company_id
]


def travel_forwards(newest_paths, all_paths):
    new_paths = []

    for path in newest_paths:
        arrows_mapping_out = network_model.get_arrows_out_of(path.to_node())
        if len(arrows_mapping_out) != 0:
            for arrow in arrows_mapping_out:
                extended_path = path.append_arrow(arrow)
                if extended_path is not None:
                    new_paths.append(extended_path)

    if len(new_paths) == 0:
        return [], all_paths
    else:
        all_paths.extend(new_paths)
        return travel_forwards(new_paths, all_paths)


empty, owns_structure = travel_forwards(owns, owns)

with open("output/owns.json", "w", encoding="utf-8") as f:
    json.dump(
        [ownership.serialize() for ownership in owns_structure],
        f,
        ensure_ascii=False,
        indent=4,
    )
