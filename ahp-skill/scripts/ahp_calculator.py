import math

RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
}

def calculate_weights(matrix):
    """
    Итеративный алгоритм поиска собственного вектора (Power Iteration).
    Возвращает (weights, CI, CR)
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
            
    ci = (cur_eigenvalue - n) / (n - 1)
    ri = RI_TABLE.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0
    return x, ci, cr

def find_most_inconsistent_comparison(matrix, weights, elements_names):
    """
    Локализация несогласованности. Находит пару, чья оценка максимально расходится с векторами.
    Возвращает (Элемент1, Элемент2, Оценка_пользователя, Идеальная_оценка)
    """
    n = len(matrix)
    max_error = 0
    worst_pair = None
    
    for i in range(n):
        for j in range(i+1, n):
            if weights[j] == 0: continue
            user_val = matrix[i][j]
            ideal_val = weights[i] / weights[j]
            # Относительная логарифмическая ошибка
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
    Идеальный режим AHP. Защита от Rank Reversal.
    """
    n_alt = len(alternative_names)
    final_scores = [0.0] * n_alt
    
    for c_name, c_weight in criteria_weights_dict.items():
        w_list = local_weights_dict[c_name]
        max_w = max(w_list) if w_list else 1
        # Делим на максимум! (В этом суть Идеального режима)
        ideal_w_list = [w / max_w for w in w_list] if max_w > 0 else w_list
        
        for i in range(n_alt):
            final_scores[i] += c_weight * ideal_w_list[i]
            
    # Нормализация для удобного отображения (сумма=1)
    s_sum = sum(final_scores)
    if s_sum > 0:
        final_scores = [s / s_sum for s in final_scores]
        
    return final_scores

def find_pareto_and_tradeoffs(local_weights, alternative_names, criteria_names):
    """
    Находит Парето-фронтир и считает дельты (компромиссы) между победителями.
    Возвращает:
      pareto_front (list)
      dominated (list)
      tradeoffs (list of dicts)
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
            
    # Tradeoffs (Компромиссы) между ВСЕМИ альтернативами на фронтире
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
                "pair": (alt_a, alt_b),
                f"advantages_of_{alt_a}": adv_a,
                f"advantages_of_{alt_b}": adv_b
            })
            
    return pareto_front, dominated, tradeoffs

def calculate_sensitivity(final_scores, criteria_weights_dict, local_weights_dict, alternative_names):
    """
    Анализ чувствительности: что должно измениться, чтобы победитель сменился.
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
    Определяет сильные и слабые стороны альтернативы (ее "ставку").
    Сильная сторона - критерий, где альтернатива имеет максимальный локальный вес среди ВСЕХ альтернатив.
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
