import dnf

def get_packages(search_term):
    base = dnf.Base()
    base.read_all_repos()
    base.fill_sack(load_system_repo=True, load_available_repos=True)

    query = base.sack.query().available().filter(name__substr=search_term)
    
    return list(query)