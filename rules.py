# Game rules for exp and levels. Change the numbers here to rebalance.
EXP_PER_CORRECT = 10
MAX_EXP_PER_GAME = 100
EXP_PER_LEVEL = 100


def exp_gain(correct_answers: int) -> int:
    return min(correct_answers * EXP_PER_CORRECT, MAX_EXP_PER_GAME)


def level_for(exp: int) -> int:
    return 1 + exp // EXP_PER_LEVEL