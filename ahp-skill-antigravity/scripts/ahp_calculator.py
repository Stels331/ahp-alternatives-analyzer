import json
import math
import sys
import os

RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
}

def calculate_weights(matrix):
    """
    Iterative power iteration to find the principal eigenvector of a matrix.
    Returns (weights, CI, CR)
    """
    n = len(matrix)
    if n == 0: return [], 0, 0
    if n == 1: return [1.0], 0, 0
        
    PRECISION = 0.0001
    MAX_ITERATIONS = 100
    
    x = [1.0 / n] * n
    cur_eigenvalue = 0.0
    prev_eigenvalue = 0.0
    
    for iteration in range(MAX_ITERATIONS):
        y = [0.0] * n
        for i in range(n):
            y[i] = sum(matrix[i][j] * x[j] for j in range(n))
            
        prev_eigenvalue = cur_eigenvalue
        cur_eigenvalue = sum(y)
        
        if cur_eigenvalue > 0:
            x = [val / cur_eigenvalue for val in y]
        else:
            break
            
        if iteration >= 1 and abs(cur_eigenvalue - prev_eigenvalue) <= PRECISION:
            break
            
    ci = (cur_eigenvalue - n) / (n - 1) if n > 1 else 0
    ri = RI_TABLE.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0
    return x, ci, cr

def find_most_inconsistent_comparison(matrix, weights, elements_names):
    """
    Finds the pairwise comparison that deviates most from the computed weights.
    Returns (Element1, Element2, user_value, ideal_value)
    """
    n = len(matrix)
    max_error = 0
    worst_pair = None
    
    for i in range(n):
        for j in range(i+1, n):
            if weights[j] == 0: continue
            user_val = matrix[i][j]
            ideal_val = weights[i] / weights[j]
            error = max(user_val / ideal_val, ideal_val / user_val) if user_val > 0 else 0
            if error > max_error:
                max_error = error
                worst_pair = (i, j, user_val, ideal_val)
                
    if worst_pair:
        i, j, u, ideal = worst_pair
        return elements_names[i], elements_names[j], u, ideal
    return None

def calculate_ideal_scores(criteria_weights_dict, local_weights_dict, alternative_names):
    """
    Ideal Mode of AHP (protects against Rank Reversal).
    """
    n_alt = len(alternative_names)
    final_scores = [0.0] * n_alt
    
    for c_name, c_weight in criteria_weights_dict.items():
        w_list = local_weights_dict[c_name]
        max_w = max(w_list) if w_list else 1.0
        # Divide by max value to get the ideal weights
        ideal_w_list = [w / max_w for w in w_list] if max_w > 0 else w_list
        
        for i in range(n_alt):
            final_scores[i] += c_weight * ideal_w_list[i]
            
    s_sum = sum(final_scores)
    if s_sum > 0:
        final_scores = [s / s_sum for s in final_scores]
        
    return final_scores

def find_pareto_and_tradeoffs(local_weights, alternative_names, criteria_names):
    """
    Computes the Pareto frontier and tradeoffs.
    """
    n_alt = len(alternative_names)
    n_crit = len(criteria_names)
    
    alt_scores = []
    for i in range(n_alt):
        alt_scores.append([local_weights[c][i] for c in criteria_names])
        
    pareto_front = []
    dominated = []
    
    for i in range(n_alt):
        is_dominated = False
        for j in range(n_alt):
            if i == j: continue
            j_gte_i = all(alt_scores[j][k] >= alt_scores[i][k] for k in range(n_crit))
            j_gt_i = any(alt_scores[j][k] > alt_scores[i][k] for k in range(n_crit))
            if j_gte_i and j_gt_i:
                is_dominated = True
                break
        if is_dominated:
            dominated.append(alternative_names[i])
        else:
            pareto_front.append(alternative_names[i])
            
    tradeoffs = []
    for i in range(len(pareto_front)):
        for j in range(i+1, len(pareto_front)):
            alt_a = pareto_front[i]
            alt_b = pareto_front[j]
            idx_a = alternative_names.index(alt_a)
            idx_b = alternative_names.index(alt_b)
            
            adv_a = []
            adv_b = []
            for c in criteria_names:
                w_a = local_weights[c][idx_a]
                w_b = local_weights[c][idx_b]
                if w_a > w_b:
                    adv_a.append((c, w_a - w_b))
                elif w_b > w_a:
                    adv_b.append((c, w_b - w_a))
                    
            tradeoffs.append({
                "pair": [alt_a, alt_b],
                f"advantages_of_{alt_a}": [{"criterion": c, "diff": diff} for c, diff in adv_a],
                f"advantages_of_{alt_b}": [{"criterion": c, "diff": diff} for c, diff in adv_b]
            })
            
    return pareto_front, dominated, tradeoffs

def calculate_sensitivity(final_scores, criteria_weights_dict, local_weights_dict, alternative_names):
    """
    Sensitivity Analysis.
    """
    if len(final_scores) < 2: return None
    
    ranked = sorted(zip(alternative_names, final_scores), key=lambda x: x[1], reverse=True)
    winner, win_score = ranked[0]
    runner_up, run_score = ranked[1]
    
    delta_score = win_score - run_score
    if delta_score == 0: return None
        
    win_idx = alternative_names.index(winner)
    run_idx = alternative_names.index(runner_up)
    
    sensitivities = []
    for c_name, c_weight in criteria_weights_dict.items():
        w_win = local_weights_dict[c_name][win_idx]
        w_run = local_weights_dict[c_name][run_idx]
        
        if w_run > w_win:
            diff = w_run - w_win
            required_increase = delta_score / diff
            sensitivities.append({
                "criterion": c_name,
                "current_weight": c_weight,
                "required_absolute_increase": required_increase,
                "percentage_increase_needed": (required_increase / c_weight * 100) if c_weight > 0 else float('inf')
            })
            
    return {
        "winner": winner,
        "runner_up": runner_up,
        "score_diff": delta_score,
        "sensitivities": sensitivities
    }

def determine_stakes(local_weights, alternative_names, criteria_names):
    """
    Stakes analysis for each alternative.
    """
    n_alt = len(alternative_names)
    stakes = {}
    for i in range(n_alt):
        strong = []
        weak = []
        for c in criteria_names:
            c_weights = local_weights[c]
            if c_weights[i] == max(c_weights):
                strong.append(c)
            if c_weights[i] == min(c_weights):
                weak.append(c)
        stakes[alternative_names[i]] = {"strong": strong, "weak": weak}
    return stakes

def generate_markdown_report(data):
    """
    Generates a clear markdown report summarizing the AHP results.
    """
    project_name = data.get("project_name", "AHP Analysis")
    goal = data.get("goal", "Choose the best alternative")
    
    lines = []
    lines.append(f"# Отчет об анализе альтернатив: {project_name}")
    lines.append(f"**Цель**: {goal}\n")
    
    lines.append("## 1. Веса критериев и согласованность")
    lines.append("| Критерий | Вес | Согласованность матрицы |")
    lines.append("| :--- | :---: | :---: |")
    criteria_weights = data.get("criteria_weights", {})
    criteria_cr = data.get("criteria_cr", 0.0)
    for c, w in criteria_weights.items():
        lines.append(f"| {c} | {w:.3f} | - |")
    lines.append(f"| **Итоговый индекс CR критериев** | - | **{criteria_cr:.3f}** |")
    lines.append("")
    
    if criteria_cr > 0.10:
        lines.append(f"> [!WARNING]")
        lines.append(f"> Коэффициент согласованности критериев CR = {criteria_cr:.3f} превышает 0.10. Оценки могут быть противоречивыми.")
        lines.append("")
        
    lines.append("## 2. Итоговый рейтинг альтернатив (Ideal Mode)")
    lines.append("| Место | Альтернатива | Итоговый балл (Score) |")
    lines.append("| :---: | :--- | :---: |")
    
    ranked_alternatives = sorted(data.get("final_scores", {}).items(), key=lambda x: x[1], reverse=True)
    for idx, (alt, score) in enumerate(ranked_alternatives, 1):
        lines.append(f"| {idx} | {alt} | {score:.3f} |")
    lines.append("")
    
    lines.append("## 3. Парето-фронтир")
    pareto_front = data.get("pareto_frontier", [])
    dominated = data.get("dominated_alternatives", [])
    
    lines.append("**Альтернативы на Парето-фронтире** (недоминируемые):")
    for alt in pareto_front:
        lines.append(f"- **{alt}**")
    lines.append("")
    
    if dominated:
        lines.append("**Доминируемые альтернативы** (уступают другим по всем показателям):")
        for alt in dominated:
            lines.append(f"- {alt}")
        lines.append("")
    else:
        lines.append("Все альтернативы находятся на Парето-фронтире. Ни одна альтернатива полностью не уступает другой.")
        lines.append("")
        
    lines.append("## 4. Стратегические ставки альтернатив")
    lines.append("| Альтернатива | Сильные стороны | Слабые стороны |")
    lines.append("| :--- | :--- | :--- |")
    alternative_bets = data.get("alternative_bets", {})
    for alt, bet in alternative_bets.items():
        strong_str = ", ".join(bet.get("strong", []))
        weak_str = ", ".join(bet.get("weak", []))
        lines.append(f"| {alt} | {strong_str} | {weak_str} |")
    lines.append("")
    
    return "\n".join(lines)

def generate_html_dashboard(data):
    """
    Generates a premium interactive HTML dashboard.
    Includes glassmorphism theme, SVG charts, and interactive Javascript sensitivity analysis.
    """
    project_name = data.get("project_name", "Анализ альтернатив AHP")
    goal = data.get("goal", "Выбрать лучший вариант")
    
    criteria_weights = data.get("criteria_weights", {})
    local_weights = data.get("alternative_local_weights", {})
    alternative_names = data.get("alternatives", [])
    criteria_names = data.get("criteria", [])
    criteria_cr = data.get("criteria_cr", 0.0)
    
    # Pre-render structures for JS
    # local_weights in python: {criterion: [val1, val2, ...]}
    # In Ideal Mode, we divide local weights by maximum weight for each criterion
    ideal_local_weights = {}
    for c in criteria_names:
        w_list = local_weights.get(c, [1.0 / len(alternative_names)] * len(alternative_names))
        max_w = max(w_list) if w_list else 1.0
        ideal_local_weights[c] = [w / max_w for w in w_list] if max_w > 0 else w_list
        
    js_data = {
        "alternatives": alternative_names,
        "criteria": criteria_names,
        "initial_weights": criteria_weights,
        "ideal_local_weights": ideal_local_weights
    }
    
    cr_color = "#10B981" if criteria_cr <= 0.10 else ("#F59E0B" if criteria_cr <= 0.20 else "#EF4444")
    cr_label = "Согласовано" if criteria_cr <= 0.10 else ("Есть сомнения" if criteria_cr <= 0.20 else "Несогласовано")
    
    # Pre-render Pareto Frontier cards to avoid nested f-strings in the main template
    pareto_cards = []
    pareto_frontier = data.get('pareto_frontier', [])
    alternative_bets = data.get('alternative_bets', {})
    for alt in alternative_names:
        is_frontier = alt in pareto_frontier
        card_class = 'frontier' if is_frontier else 'dominated'
        badge_text = 'Парето-фронтир' if is_frontier else 'Доминируется'
        desc_text = "Сильный компромиссный выбор." if is_frontier else "Уступает другим решениям по всем критериям."
        
        bets = alternative_bets.get(alt, {})
        strong_criteria = ", ".join(bets.get('strong', []))
        weak_criteria = ", ".join(bets.get('weak', []))
        
        card_html = f"""
                <div class="pareto-card {card_class}">
                    <span class="pareto-badge">{badge_text}</span>
                    <h3 class="pareto-title">{alt}</h3>
                    <p class="pareto-desc">{desc_text}</p>
                    <div style="margin-top: 0.75rem; font-size: 0.85rem;">
                        <strong>Сильные критерии:</strong> <span style="color: var(--success);">{strong_criteria}</span><br/>
                        <strong>Слабые критерии:</strong> <span style="color: var(--danger);">{weak_criteria}</span>
                    </div>
                </div>"""
        pareto_cards.append(card_html)
    pareto_cards_html = "".join(pareto_cards)

    # Pre-render Tradeoffs HTML block
    tradeoffs_html = ""
    if data.get('tradeoffs'):
        tradeoff_boxes = []
        for t in data.get('tradeoffs', []):
            pair_a, pair_b = t['pair'][0], t['pair'][1]
            adv_a_list = t.get(f"advantages_of_{pair_a}", [])
            adv_b_list = t.get(f"advantages_of_{pair_b}", [])
            
            adv_a_strs = [f"{a['criterion']} (+{a['diff']:.2%})" for a in adv_a_list]
            adv_b_strs = [f"{a['criterion']} (+{a['diff']:.2%})" for a in adv_b_list]
            
            adv_a_txt = ", ".join(adv_a_strs) if adv_a_strs else "нет"
            adv_b_txt = ", ".join(adv_b_strs) if adv_b_strs else "нет"
            
            box_html = f"""
            <div class="tradeoff-box">
                <div class="tradeoff-pair">{pair_a} vs {pair_b}</div>
                <div class="tradeoff-detail">
                    <strong>Преимущества {pair_a}:</strong> {adv_a_txt}
                </div>
                <div class="tradeoff-detail">
                    <strong>Преимущества {pair_b}:</strong> {adv_b_txt}
                </div>
            </div>"""
            tradeoff_boxes.append(box_html)
            
        tradeoffs_inner = "".join(tradeoff_boxes)
        tradeoffs_html = f"""
        <div class="glass-card">
            <h2 class="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-git-pull-request"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M6 9v12"/></svg>
                Непосредственные компромиссы (Trade-offs)
            </h2>
            {tradeoffs_inner}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - AHP Дашборд</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            --glass-bg: rgba(30, 41, 59, 0.45);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #6366f1;
            --accent-secondary: #ec4899;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --font-main: 'Inter', sans-serif;
            --font-display: 'Outfit', sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background: var(--bg-gradient);
            color: var(--text-main);
            font-family: var(--font-main);
            min-height: 100vh;
            padding: 2rem 1.5rem;
            line-height: 1.5;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Glassmorphism Card Style */
        .glass-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            box-shadow: var(--glass-shadow);
            padding: 2rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }}

        .glass-card:hover {{
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }}

        /* Header Layout */
        header.project-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1.5rem;
        }}

        .header-content h1 {{
            font-family: var(--font-display);
            font-size: 2.25rem;
            font-weight: 700;
            background: linear-gradient(to right, #818cf8, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .header-content p {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        .cr-badge {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
        }}

        .cr-badge .value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--cr-color);
            line-height: 1.2;
        }}

        .cr-badge .label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}

        /* Main Dashboard Grid */
        .grid-layout {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }}

        @media (min-width: 900px) {{
            .grid-layout {{
                grid-template-columns: 1.2fr 1fr;
            }}
        }}

        /* Rankings and Charts */
        .section-title {{
            font-family: var(--font-display);
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 0.75rem;
        }}

        .ranking-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .ranking-item {{
            display: flex;
            align-items: center;
            padding: 1rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            transition: all 0.2s ease;
        }}

        .ranking-item.winner {{
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.05) 100%);
            border-color: rgba(99, 102, 241, 0.3);
        }}

        .rank-num {{
            font-family: var(--font-display);
            font-size: 1.75rem;
            font-weight: 700;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.05);
            margin-right: 1rem;
        }}

        .winner .rank-num {{
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
            color: #fff;
        }}

        .rank-details {{
            flex-grow: 1;
        }}

        .rank-name {{
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 0.25rem;
        }}

        .rank-bar-bg {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            overflow: hidden;
        }}

        .rank-bar-fill {{
            height: 100%;
            background: var(--accent-primary);
            border-radius: 4px;
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .winner .rank-bar-fill {{
            background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
        }}

        .rank-val {{
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 1.25rem;
            margin-left: 1.5rem;
            min-width: 60px;
            text-align: right;
        }}

        /* Sensitivity Sliders */
        .slider-group {{
            margin-bottom: 1.25rem;
        }}

        .slider-header {{
            display: flex;
            justify-content: space-between;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }}

        .slider-name {{
            font-weight: 500;
        }}

        .slider-val {{
            color: var(--accent-primary);
            font-weight: 600;
        }}

        .slider-control {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .slider-input {{
            flex-grow: 1;
            -webkit-appearance: none;
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.1);
            outline: none;
            transition: background 0.3s;
        }}

        .slider-input::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--accent-primary);
            cursor: pointer;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
            transition: transform 0.1s ease;
        }}

        .slider-input::-webkit-slider-thumb:hover {{
            transform: scale(1.2);
        }}

        /* Pareto Section */
        .pareto-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }}

        .pareto-card {{
            padding: 1.5rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.015);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .pareto-card.frontier {{
            border-left: 4px solid var(--success);
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
        }}

        .pareto-card.dominated {{
            border-left: 4px solid var(--text-muted);
            opacity: 0.65;
        }}

        .pareto-badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }}

        .frontier .pareto-badge {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }}

        .dominated .pareto-badge {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
        }}

        .pareto-title {{
            font-family: var(--font-display);
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .pareto-desc {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}

        /* Buttons & Actions */
        .reset-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem 1.2rem;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: var(--text-main);
            font-family: var(--font-main);
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 1rem;
        }}

        .reset-btn:hover {{
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }}

        /* Tradeoffs section */
        .tradeoff-box {{
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 1.25rem;
            margin-top: 1rem;
        }}

        .tradeoff-pair {{
            font-weight: 600;
            color: #818cf8;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
        }}

        .tradeoff-detail {{
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            padding-left: 1rem;
            border-left: 2px solid rgba(255, 255, 255, 0.08);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="glass-card" style="margin-bottom: 1.5rem;">
            <header class="project-header">
                <div class="header-content">
                    <h1>{project_name}</h1>
                    <p>Цель: {goal}</p>
                </div>
                <div class="cr-badge" style="--cr-color: {cr_color}">
                    <span class="value">{criteria_cr:.3f}</span>
                    <span class="label">CR критериев ({cr_label})</span>
                </div>
            </header>
        </div>

        <!-- Main Workspace -->
        <div class="grid-layout">
            <!-- Left: Rankings Calculator -->
            <div class="glass-card">
                <h2 class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-award"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>
                    Текущие результаты (AHP Ideal Mode)
                </h2>
                <div class="ranking-list" id="rankings-container">
                    <!-- Dynamic rendering by JS -->
                </div>
            </div>

            <!-- Right: Interactive Sensitivity Analysis -->
            <div class="glass-card">
                <h2 class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sliders"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/></svg>
                    Симулятор чувствительности
                </h2>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">
                    Передвигайте ползунки, чтобы настроить важность критериев. Итоговый рейтинг альтернатив слева пересчитается мгновенно. Веса остальных критериев автоматически адаптируются.
                </p>
                <div id="sliders-container">
                    <!-- Sliders render here -->
                </div>
                <button class="reset-btn" id="reset-btn">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
                    Сбросить веса к исходным
                </button>
            </div>
        </div>

        <!-- Pareto Frontier section -->
        <div class="glass-card">
            <h2 class="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-grid"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
                Граница Парето (Доминирование)
            </h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1rem;">
                Анализ пограничных альтернатив. Варианты на Парето-фронтире обладают уникальными преимуществами. Доминируемые варианты уступают другим по всем критериям и математически неоптимальны.
            </p>
            <div class="pareto-grid">
                <!-- Cards render here -->
                {pareto_cards_html}
            </div>
        </div>

        <!-- Tradeoffs & Strategic Bets -->
        {tradeoffs_html}
    </div>

    <!-- Script logic -->
    <script>
        const projectData = {json.dumps(js_data, ensure_ascii=False)};
        
        let currentWeights = {{ ...projectData.initial_weights }};
        
        function initSliders() {{
            const container = document.getElementById('sliders-container');
            container.innerHTML = '';
            
            projectData.criteria.forEach(criterion => {{
                const weight = currentWeights[criterion] || 0;
                
                const group = document.createElement('div');
                group.className = 'slider-group';
                
                group.innerHTML = `
                    <div class="slider-header">
                        <span class="slider-name">${{criterion}}</span>
                        <span class="slider-val" id="val-${{criterion}}">${{(weight * 100).toFixed(1)}}%</span>
                    </div>
                    <div class="slider-control">
                        <input type="range" class="slider-input" 
                                id="slider-${{criterion}}" 
                                min="0" max="1" step="0.01" 
                                value="${{weight}}">
                    </div>
                `;
                
                container.appendChild(group);
                
                const slider = group.querySelector('input');
                slider.addEventListener('input', (e) => {{
                    handleSliderChange(criterion, parseFloat(e.target.value));
                }});
            }});
        }}
        
        function handleSliderChange(changedCrit, newValue) {{
            const oldValue = currentWeights[changedCrit];
            if (newValue === 1) {{
                // All other weights become 0
                projectData.criteria.forEach(c => {{
                    currentWeights[c] = (c === changedCrit) ? 1.0 : 0.0;
                }});
            }} else {{
                currentWeights[changedCrit] = newValue;
                const sumOthers = projectData.criteria
                    .filter(c => c !== changedCrit)
                    .reduce((sum, c) => sum + currentWeights[c], 0);
                
                const targetSumOthers = 1.0 - newValue;
                
                projectData.criteria.forEach(c => {{
                    if (c !== changedCrit) {{
                        if (sumOthers > 0) {{
                            currentWeights[c] = (currentWeights[c] / sumOthers) * targetSumOthers;
                        }} else {{
                            // Distribute evenly if all others were 0
                            currentWeights[c] = targetSumOthers / (projectData.criteria.length - 1);
                        }}
                    }}
                }});
            }}
            
            updateUI();
        }}
        
        function calculateFinalScores() {{
            const scores = new Array(projectData.alternatives.length).fill(0.0);
            
            projectData.criteria.forEach(criterion => {{
                const cWeight = currentWeights[criterion] || 0;
                const localWList = projectData.ideal_local_weights[criterion] || [];
                
                for (let i = 0; i < scores.length; i++) {{
                    scores[i] += cWeight * (localWList[i] || 0);
                }}
            }});
            
            const sum = scores.reduce((s, val) => s + val, 0);
            if (sum > 0) {{
                return scores.map(s => s / sum);
            }}
            return scores;
        }}
        
        function updateUI() {{
            // 1. Update sliders values
            projectData.criteria.forEach(c => {{
                const valSpan = document.getElementById(`val-${{c}}`);
                const slider = document.getElementById(`slider-${{c}}`);
                
                const w = currentWeights[c];
                valSpan.textContent = `${{(w * 100).toFixed(1)}}%`;
                slider.value = w;
            }});
            
            // 2. Recalculate scores
            const scores = calculateFinalScores();
            
            const ranked = projectData.alternatives.map((alt, idx) => ({{
                name: alt,
                score: scores[idx]
            }})).sort((a, b) => b.score - a.score);
            
            // 3. Render rankings list
            const rankingsContainer = document.getElementById('rankings-container');
            rankingsContainer.innerHTML = '';
            
            ranked.forEach((item, index) => {{
                const maxScore = ranked[0].score || 1.0;
                const relativeWidth = maxScore > 0 ? (item.score / maxScore * 100) : 0;
                
                const itemDiv = document.createElement('div');
                itemDiv.className = `ranking-item ${{index === 0 ? 'winner' : ''}}`;
                
                itemDiv.innerHTML = `
                    <div class="rank-num">${{index + 1}}</div>
                    <div class="rank-details">
                        <div class="rank-name">${{item.name}}</div>
                        <div class="rank-bar-bg">
                            <div class="rank-bar-fill" style="width: ${{relativeWidth}}%"></div>
                        </div>
                    </div>
                    <div class="rank-val">${{(item.score).toFixed(3)}}</div>
                `;
                
                rankingsContainer.appendChild(itemDiv);
            }});
        }}
        
        document.getElementById('reset-btn').addEventListener('click', () => {{
            currentWeights = {{ ...projectData.initial_weights }};
            updateUI();
        }});
        
        // Initial build
        initSliders();
        updateUI();
    </script>
</body>
</html>
"""
    return html

def run_calculator(project_file):
    """
    Main function to load project, perform AHP logic, and generate outputs.
    """
    if not os.path.exists(project_file):
        print(f"Error: file {project_file} not found.")
        sys.exit(1)
        
    with open(project_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Extract structural names
    criteria = data.get("criteria", [])
    alternatives = data.get("alternatives", [])
    
    n_crit = len(criteria)
    n_alt = len(alternatives)
    
    # 1. Build and calculate criteria weights
    # criteria_judgments is a square matrix or list of comparisons
    # If saved as a matrix:
    criteria_matrix = data.get("criteria_matrix")
    if not criteria_matrix and "criteria_judgments" in data:
        # Build matrix from judgments list
        criteria_matrix = [[1.0] * n_crit for _ in range(n_crit)]
        for jg in data["criteria_judgments"]:
            # item_a, item_b, selected, intensity
            try:
                idx_a = criteria.index(jg["item_a"])
                idx_b = criteria.index(jg["item_b"])
                intensity = float(jg["intensity"])
                
                if jg["selected"] == jg["item_a"]:
                    criteria_matrix[idx_a][idx_b] = intensity
                    criteria_matrix[idx_b][idx_a] = 1.0 / intensity
                else:
                    criteria_matrix[idx_b][idx_a] = intensity
                    criteria_matrix[idx_a][idx_b] = 1.0 / intensity
            except ValueError:
                continue
                
    if criteria_matrix:
        c_weights, c_ci, c_cr = calculate_weights(criteria_matrix)
        data["criteria_matrix"] = criteria_matrix
        data["criteria_weights"] = {criteria[i]: c_weights[i] for i in range(n_crit)}
        data["criteria_cr"] = c_cr
    else:
        # Defaults if no comparison yet
        data["criteria_weights"] = {c: 1.0 / n_crit for c in criteria}
        data["criteria_cr"] = 0.0
        
    # 2. Build and calculate alternative weights per criterion
    local_weights_dict = {}
    alt_crs = {}
    for c in criteria:
        # Check if alternative judgments exist for this criterion
        alt_matrix = None
        if "alternative_matrices" in data and c in data["alternative_matrices"]:
            alt_matrix = data["alternative_matrices"][c]
        elif "alternative_judgments" in data and c in data["alternative_judgments"]:
            alt_matrix = [[1.0] * n_alt for _ in range(n_alt)]
            for jg in data["alternative_judgments"][c]:
                try:
                    idx_a = alternatives.index(jg["item_a"])
                    idx_b = alternatives.index(jg["item_b"])
                    intensity = float(jg["intensity"])
                    
                    if jg["selected"] == jg["item_a"]:
                        alt_matrix[idx_a][idx_b] = intensity
                        alt_matrix[idx_b][idx_a] = 1.0 / intensity
                    else:
                        alt_matrix[idx_b][idx_a] = intensity
                        alt_matrix[idx_a][idx_b] = 1.0 / intensity
                except ValueError:
                    continue
                    
        if alt_matrix:
            a_weights, a_ci, a_cr = calculate_weights(alt_matrix)
            if "alternative_matrices" not in data:
                data["alternative_matrices"] = {}
            data["alternative_matrices"][c] = alt_matrix
            local_weights_dict[c] = a_weights
            alt_crs[c] = a_cr
        else:
            # Defaults
            local_weights_dict[c] = [1.0 / n_alt] * n_alt
            alt_crs[c] = 0.0
            
    data["alternative_local_weights"] = local_weights_dict
    data["alternative_crs"] = alt_crs
    
    # 3. Calculate final rankings using Ideal Mode
    final_scores = calculate_ideal_scores(data["criteria_weights"], local_weights_dict, alternatives)
    data["final_scores"] = {alternatives[i]: final_scores[i] for i in range(n_alt)}
    
    # 4. Find Pareto frontier and tradeoffs
    pareto_front, dominated, tradeoffs = find_pareto_and_tradeoffs(local_weights_dict, alternatives, criteria)
    data["pareto_frontier"] = pareto_front
    data["dominated_alternatives"] = dominated
    data["tradeoffs"] = tradeoffs
    
    # 5. Determine stakes
    stakes = determine_stakes(local_weights_dict, alternatives, criteria)
    data["alternative_bets"] = stakes
    
    # 6. Sensitivity Analysis
    sensitivity = calculate_sensitivity(final_scores, data["criteria_weights"], local_weights_dict, alternatives)
    data["sensitivity_analysis"] = sensitivity
    
    # Save back to json file
    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    # Generate reports in same directory as project_file
    base_dir = os.path.dirname(project_file)
    
    md_content = generate_markdown_report(data)
    md_file = os.path.join(base_dir, "ahp_report.md")
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    html_content = generate_html_dashboard(data)
    html_file = os.path.join(base_dir, "ahp_dashboard.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Calculations complete.")
    print(f"Updated state: {project_file}")
    print(f"Markdown report generated: {md_file}")
    print(f"Interactive HTML dashboard generated: {html_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ahp_calculator.py <path_to_project_json>")
        sys.exit(1)
    run_calculator(sys.argv[1])
