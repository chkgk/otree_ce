from otree.api import *
from collections import Counter
import json

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'titration'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5

    LOTTERY_HIGH = cu(100)
    LOTTERY_LOW = cu(0)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    choose_sure = models.BooleanField(
        choices=[(False, "Lottery"), (True, "Sure Amount")],
        Label="Lottery or Sure Amount?"
    )
    ce_estimate = models.CurrencyField()


# FUNCTIONS
def creating_session(subsession):
    if subsession.round_number == 1:
        for p in subsession.get_players():
            p.ce_estimate = (C.LOTTERY_HIGH + C.LOTTERY_LOW) / 2


def update_ce_estimate(player):
    rn = player.round_number
    adjustment = (C.LOTTERY_HIGH + C.LOTTERY_LOW) / 2 ** (rn + 1)
    if player.choose_sure:
        player.ce_estimate -= adjustment
    else:
        player.ce_estimate += adjustment

    if rn < C.NUM_ROUNDS:
        player.in_round(rn + 1).ce_estimate = player.ce_estimate


def vars_for_admin_report(subsession):
    ce_estimates = []
    for p in subsession.get_players():
        if p.round_number == C.NUM_ROUNDS:
            if p.field_maybe_none("ce_estimate") is not None:
                ce_estimates.append(p.ce_estimate)
    mean_ce = sum(ce_estimates) / len(ce_estimates)
    median_ce = sorted(ce_estimates)[len(ce_estimates) // 2]
    non_currency_ce = [float(ce) for ce in ce_estimates]

    ce_estimate_dict = dict(Counter(non_currency_ce))
    sorted_dict = dict(sorted(ce_estimate_dict.items()))
    
    return {
        'expected_value': (C.LOTTERY_HIGH + C.LOTTERY_LOW) / 2,
        'mean_ce': mean_ce,
        'median_ce': median_ce,
        'ce_values': json.dumps(list(sorted_dict.keys())),
        'ce_frequencies': json.dumps(list(sorted_dict.values()))
    }

# PAGES
class Intro(Page):
    def is_displayed(self):
        return self.round_number == 1


class Titration(Page):
    form_model = 'player'
    form_fields = ['choose_sure']

    def before_next_page(player, timeout_happened):
        update_ce_estimate(player)


class Results(Page):
    def vars_for_template(player):
        return {
            'expected_value': (C.LOTTERY_HIGH + C.LOTTERY_LOW) / 2,
        }

    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [Intro, Titration, Results]
