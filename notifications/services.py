from payments.models import Payment


def get_bot_debtors_text():
    debts = Payment.objects.filter(status="debt").select_related("student")
    if not debts.exists():
        return "Боржників немає 🎉"
    lines = [f"• {p.student.full_name} — {p.amount} грн" for p in debts]
    return "Боржники:\n" + "\n".join(lines)
