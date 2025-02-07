import json


with open('data/ResightsApS.json', 'r') as f:
    network = json.load(f)

    


# CODE:


# --- MODEL ---

class Company:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.ownerships = []
    
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

class CompanyMap:
    companies = dict()
    distance_to_focus_point = dict()

    def has_company(self, id):
        return id in self.companies.keys()
    
    def add_company(self, company):
        self.companies[company.id] = company
    
    def add_source_and_target(self, ownership_descriptor):
        if (not self.has_company(str(ownership_descriptor['source']))):
            self.add_company(Company(ownership_descriptor['source'], ownership_descriptor['source_name']))
        if (not self.has_company(str(ownership_descriptor['target']))):
            self.add_company(Company(ownership_descriptor['target'], ownership_descriptor['target_name']))
    
    def serialize(self):
        return dict([(k, v.serialize()) for k, v in self.companies.items()])


class Ownership:
    def __init__(self, id, source, target, ownership_string):
        self.id = id
        self.source = source
        self.target = target
        
        self.direct_ownership_lower = self.parse_ownership(ownership_string)[0]
        self.direct_ownership_upper = self.parse_ownership(ownership_string)[1]
    

    def direct_ownership_average(self):
        return (self.direct_ownership_lower + self.direct_ownership_upper) / 2


    # Expected shape of ownership string i "dd-dd%" OR "dd%"
    def parse_ownership(_self, ownership):
        parts = ownership.split('-')

        start = float(remove_percentage_sign(parts[0]))
        if len(parts) == 1:
            return [start, start]
        elif len(parts) == 2:
            return [start, float(remove_percentage_sign(parts[1]))]
    

    def serialize(self):
        return {
            'source': self.source,
            'target': self.target,
            'direct_ownership_lower': self.direct_ownership_lower,
            'direct_ownership_average': self.direct_ownership_average(),
            'direct_ownership_upper': self.direct_ownership_upper
        }


class OwnershipMap:
    ownerships = dict()
    ownership_to = dict()
    ownership_from = dict()

    def has_ownership(self, id):
        return id in self.ownerships.keys()
    


    def add_ownership(self, ownership_descriptor):
        if (not self.has_ownership(str(ownership_descriptor['id']))):
            ownership_model = Ownership(
                ownership_descriptor['id'], 
                ownership_descriptor['source'], 
                ownership_descriptor['target'], 
                ownership_descriptor['share']
            )
            self.ownerships[ownership_descriptor['id']] = ownership_model
            self.add_ownership_to(ownership_model)
            self.add_ownership_from(ownership_model)
    
    def add_ownership_to(self, ownership):
        identifier = ownership.target

        if identifier not in self.ownership_to:
            self.ownership_to[identifier] = [ownership]
        self.ownership_to[identifier].append(ownership)

    def add_ownership_from(self, ownership):
        identifier = ownership.source

        if identifier not in self.ownership_from:
            self.ownership_to[identifier] = [ownership]
        self.ownership_to[identifier].append(ownership)

    def serialize(self):
        return dict([(k, v.serialize()) for k, v in self.ownerships.items()])
    

class OwnershipPath:
    path = []
    
    lower_weight = 1
    upper_weight = 1
    
    def __init__(self,path, lower_weight = 1, upper_weight = 1):
        self.path = path

    @classmethod
    def start(cls, ownership):
        return cls([ownership.source, ownership.target])
    
    def first(self):
        return self.path[0]
    
    def last(self):
        return self.path[-1]

    def close_as_loop(self):
        self.lower_weight = 0
        self.upper_weight = 0

    def append_ownership(self, ownership):
        if self.last() != ownership.source:
            raise ValueError('Ownership does not match source company')
        if ownership.target in self.path:
            self.close_as_loop()
            return
        if self.is_closed():
            return

        new_path = self.path + [ownership]
        
        return OwnershipPath(
            new_path, 
            self.lower_weight * ownership.direct_ownership_lower, 
            self.upper_weight * ownership.direct_ownership_upper
        )
    
    
    def prepend_ownership(self, ownership):
        if self.first() != ownership.target:
            print(self.path, ownership.serialize())
            raise ValueError('Ownership does not match target company')
        if ownership.source in self.path:
            self.close_as_loop()
            return
        if self.is_closed():
            return

        new_path = [ownership] + self.path
        return OwnershipPath(
            new_path, 
            self.lower_weight * ownership.direct_ownership_lower, 
            self.upper_weight * ownership.direct_ownership_upper
        )
    
    def is_closed(self):
        return self.lower_weight == 0 and self.upper_weight == 0


# --- HELPERS ---
def remove_percentage_sign(string):
    return string.split('%')[0]


# --- PROCESSING ---
company_map = CompanyMap()
ownership_map = OwnershipMap()

# Load companies and direct ownerships
for company_ownership in network:
     company_map.add_source_and_target(company_ownership)
     ownership_map.add_ownership(company_ownership)


owned_by = [OwnershipPath.start(ownership) for ownership in ownership_map.ownership_to[41527080]]

active_paths = [path for path in owned_by if not path.is_closed()]
inactive_paths = [path for path in owned_by if path.is_closed()]

def travel_backwards(active_paths, inactive_paths):
    if len(active_paths) == 0:
        return [active_paths, inactive_paths]

    new_paths = []
    for active_path in active_paths:
        for ownership in ownership_map.ownership_to[active_path.first()]:
            new_paths.append(active_path.prepend_ownership(ownership))

    new_active_paths = [path for path in new_paths if not path.is_closed()]
    new_inactive_paths = [path for path in new_paths if path.is_closed()]

    return travel_backwards(new_active_paths, inactive_paths + new_inactive_paths)

empty, final_structure = travel_backwards(active_paths, inactive_paths)

# --- WRITE TO FILE(S)

with open('isOwnedBy.json', 'w', encoding='utf-8') as f:
    json.dump([ownership.path for ownership in final_structure], f, ensure_ascii=False, indent=4)

#with open('ownership.json', 'w', encoding='utf-8') as f:
#    json.dump(ownership_map.serialize(), f, ensure_ascii=False, indent=4)




