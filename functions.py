def remove_VRBO_from_partner_name(partner):
    if not 'VRBO' in partner: return partner
    return partner[7:]


def get_target_email_from_partner_situations(partner, sets):

    df = sets[sets.PARTNER == partner]
    situations = df.SITUATION.values

    # for situation in situations:
    #     if 'CARILLON' in situation.upper(): return 'carillonbeach@vacayzen.com'

    return 'partners@vacayzen.com'

def is_unit_valid(row, units):
    return row.Unit in units