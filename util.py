from model.TrooperStance import TrooperStance
import params

def CanShoot(me, enemy, world):
  return world.is_visible(me.shooting_range, me.x, me.y, me.stance, enemy.x, enemy.y, enemy.stance)


def MoveCost(trooper, game):
  if trooper.stance == TrooperStance.STANDING:
    return game.standing_move_cost
  elif trooper.stance == TrooperStance.KNEELING:
    return game.kneeling_move_cost
  else:
    assert trooper.stance == TrooperStance.PRONE
    return game.prone_move_cost


def ShootDamage(trooper):
  if trooper.stance == TrooperStance.STANDING:
    return trooper.standing_damage
  elif trooper.stance == TrooperStance.KNEELING:
    return trooper.kneeling_damage
  else:
    assert trooper.stance == TrooperStance.PRONE
    return trooper.prone_damage


def ComputeDamage(enemy, dmg):
  assert enemy is not None
  realdmg = min(dmg, enemy.hitpoints)
  return realdmg + params.KILL_EXTRA_PROFIT if realdmg == enemy.hitpoints else realdmg

