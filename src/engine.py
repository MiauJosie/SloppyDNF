import dnf


def get_all():
    base = dnf.Base()
    base.read_all_repos()
    base.fill_sack(load_system_repo=True, load_available_repos=True)

    available = list(base.sack.query().available())
    installed = list(base.sack.query().installed())
    upgrades = list(base.sack.query().upgrades())

    return available, installed, upgrades
