from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from scipy.stats import binom

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    graph_url = None
    form_values = {}

    if request.method == 'POST':
        form_values = {key: request.form[key] for key in request.form}

        try:
            # Get values from form
            time_steps = int(form_values.get("time_steps", 10))
            n_seats_coach = int(form_values.get("n_seats_coach", 100))
            overbook_limit = int(form_values.get("overbook_coach", 10))
            n_seats_first = int(form_values.get("n_seats_first", 20))
            discount = float(form_values.get("discount", 0.999))

            showup_prob_coach = float(form_values.get("showup_prob_coach", 0.95))
            showup_prob_first = float(form_values.get("showup_prob_first", 0.97))

            price_coach = [int(form_values.get("price_coach_low", 300)), int(form_values.get("price_coach_high", 350))]
            prob_coach = [float(form_values.get("prob_coach_low", 0.65)), float(form_values.get("prob_coach_high", 0.30))]

            price_first = [int(form_values.get("price_first_low", 425)), int(form_values.get("price_first_high", 500))]
            prob_first = [float(form_values.get("prob_first_low", 0.08)), float(form_values.get("prob_first_high", 0.04))]

            coach_price_boost = float(form_values.get("coach_price_boost", 0.03))
            cost_upgrade = float(form_values.get("cost_upgrade", 30))
            cost_off = float(form_values.get("cost_off", 100))

            apply_seasonality = form_values.get("apply_seasonality", "True") == "True"
            has_option_to_not_sell = form_values.get("has_option_to_not_sell", "True") == "True"

            graph_url, result = generate_policy_plot(
                overbook_limit, time_steps, n_seats_coach, n_seats_first,
                discount, showup_prob_coach, showup_prob_first,
                price_coach, prob_coach, price_first, prob_first,
                coach_price_boost, cost_upgrade, cost_off,
                apply_seasonality, has_option_to_not_sell
            )

        except Exception as e:
            result = f"Error: {e}"

    return render_template("index.html", result=result, graph_url=graph_url, form_values=form_values)

def policy(overbooked_seats, time_steps, n_coach, n_first, discount,
           showup_prob_coach, showup_prob_first,
           price_coach, prob_coach, price_first, prob_first,
           coach_price_boost, cost_upgrade, cost_off,
           apply_seasonality, has_option_to_not_sell):

    N_COACH = n_coach + overbooked_seats
    V = np.zeros((time_steps+1, N_COACH+1, n_first+1))
    U = np.zeros((time_steps+1, N_COACH+1, n_first+1))

    for c in range(N_COACH+1):
        for f in range(n_first+1):
            exp_cost = 0
            for i in range(n_coach+1, c+1):
                for j in range(f+1):
                    extra = max(i - n_coach, 0)
                    upgrades = min(n_first - j, extra)
                    cost = upgrades * cost_upgrade + (extra - upgrades) * cost_off
                    prob = binom.pmf(i, c, showup_prob_coach) * binom.pmf(j, f, showup_prob_first)
                    exp_cost += cost * prob
            V[time_steps, c, f] = -exp_cost
            U[time_steps, c, f] = -1

    for t in reversed(range(time_steps)):
        for c in range(N_COACH+1):
            for f in range(n_first+1):
                profits = []
                for pc in range(2):
                    for pf in range(2):
                        ep = 0
                        for sc in range(2):
                            for sf in range(2):
                                prob_c = prob_coach[pc] * (0.75 + t / 730 if apply_seasonality else 1)
                                prob_f = prob_first[pf] * (0.75 + t / 730 if apply_seasonality else 1)
                                if f == n_first:
                                    prob_c += coach_price_boost
                                    prob_f = 0
                                if c == N_COACH:
                                    prob_c = 0
                                pc_prob = prob_c if sc else 1 - prob_c
                                pf_prob = prob_f if sf else 1 - prob_f
                                prob = pc_prob * pf_prob
                                next_c, next_f = min(c+sc, N_COACH), min(f+sf, n_first)
                                reward = sc * price_coach[pc] + sf * price_first[pf]
                                future = V[t+1, next_c, next_f]
                                ep += prob * (reward + discount * future)
                        profits.append(ep)
                if has_option_to_not_sell:
                    for pf in range(2):
                        ep = 0
                        for sf in range(2):
                            prob_f = prob_first[pf] * (0.75 + t / 730 if apply_seasonality else 1)
                            if f == n_first:
                                prob_f = 0
                            pf_prob = prob_f if sf else 1 - prob_f
                            next_f = min(f+sf, n_first)
                            reward = sf * price_first[pf]
                            future = V[t+1, c, next_f]
                            ep += pf_prob * (reward + discount * future)
                        profits.append(ep)
                V[t, c, f] = max(profits)
                U[t, c, f] = np.argmax(profits)
    return V, U

def generate_policy_plot(overbook_limit, *args):
    V_dict = {}
    for ob in range(1, overbook_limit + 1):
        V, _ = policy(ob, *args)
        V_dict[ob] = V[0, 0, 0]

    fig, ax = plt.subplots()
    ax.plot(list(V_dict.keys()), list(V_dict.values()), marker='o')
    ax.set_xlabel('Allowed Coach Overbook')
    ax.set_ylabel('Expected Present Value')
    ax.set_title('Expected Present Value vs Overbook Coach')
    ax.grid(True)

    best = max(V_dict, key=V_dict.get)
    return convert_plot_to_base64(fig), f"Best overbook policy is {best} seats with expected value ${V_dict[best]:,.2f}"

def convert_plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return f'data:image/png;base64,{base64.b64encode(buf.read()).decode("utf-8")}'

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

