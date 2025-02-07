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

    def has_ownership(self, id):
        return id in self.ownerships.keys()

    def add_ownership(self, ownership_descriptor):
        if (not self.has_ownership(str(ownership_descriptor['id']))):
            self.ownerships[ownership_descriptor['id']] = Ownership(
                ownership_descriptor['id'], 
                ownership_descriptor['source'], 
                ownership_descriptor['target'], 
                ownership_descriptor['share']
            )

    def serialize(self):
        return dict([(k, v.serialize()) for k, v in self.ownerships.items()])


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


with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(company_map.serialize(), f, ensure_ascii=False, indent=4)

with open('ownership.json', 'w', encoding='utf-8') as f:
    json.dump(ownership_map.serialize(), f, ensure_ascii=False, indent=4)




