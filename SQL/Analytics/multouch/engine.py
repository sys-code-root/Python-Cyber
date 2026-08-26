from schemas import ValidatedJourney

class AttributionEngine:
    def __init__(self, journeys: list[ValidatedJourney], costs: dict[str, float]):
        self.journeys = journeys
        self.costs = costs
        self.channels = list(costs.keys())

    def compute_first_click(self) -> dict[str, float]:
        allocation = {c: 0.0 for c in self.channels}
        for j in self.journeys:
            if j.converted == 1 and j.touchpoints:
                first_ch = j.touchpoints[0]
                if first_ch in allocation:
                    allocation[first_ch] += j.revenue
        return allocation

    def compute_last_click(self) -> dict[str, float]:
        allocation = {c: 0.0 for c in self.channels}
        for j in self.journeys:
            if j.converted == 1 and j.touchpoints:
                last_ch = j.touchpoints[-1]
                if last_ch in allocation:
                    allocation[last_ch] += j.revenue
        return allocation

    def compute_linear(self) -> dict[str, float]:
        allocation = {c: 0.0 for c in self.channels}
        for j in self.journeys:
            if j.converted == 1 and j.touchpoints:
                n = len(j.touchpoints)
                split_rev = j.revenue / n
                for ch in j.touchpoints:
                    if ch in allocation:
                        allocation[ch] += split_rev
        return allocation

    def compute_time_decay(self, half_life_days: float = 7.0) -> dict[str, float]:
        allocation = {c: 0.0 for c in self.channels}
        for j in self.journeys:
            if j.converted == 1 and j.touchpoints:
                t_max = j.timestamps[-1]
                weights = []
                for t in j.timestamps:
                    days_diff = (t_max - t) / 86400.0
                    w = 2 ** (-days_diff / half_life_days)
                    weights.append(w)
                
                total_w = sum(weights)
                if total_w == 0:
                    total_w = 1.0
                
                for ch, w in zip(j.touchpoints, weights):
                    if ch in allocation:
                        allocation[ch] += (w / total_w) * j.revenue
        return allocation

    def compute_data_driven_markov(self) -> dict[str, float]:
        allocation = {c: 0.0 for c in self.channels}
        transition_counts = {}
        
        for j in self.journeys:
            path = ["(Start)"]
            for ch in j.touchpoints:
                if not path or path[-1] != ch:
                    path.append(ch)
            
            if j.converted == 1:
                path.append("(Conversion)")
            else:
                path.append("(Dropoff)")
                
            for i in range(len(path) - 1):
                state_from = path[i]
                state_to = path[i+1]
                if state_from not in transition_counts:
                    transition_counts[state_from] = {}
                transition_counts[state_from][state_to] = transition_counts[state_from].get(state_to, 0) + 1

        transition_matrix = {}
        for state_from, targets in transition_counts.items():
            total_outventions = sum(targets.values())
            transition_matrix[state_from] = {st: count / total_outventions for st, count in targets.items()}

        def calculate_conversion_probability(matrix_instance) -> float:
            state_probs = {"(Start)": 1.0}
            for _ in range(15):
                next_probs = {}
                for s, p in state_probs.items():
                    if s in ["(Conversion)", "(Dropoff)"]:
                        next_probs[s] = next_probs.get(s, 0.0) + p
                        continue
                    if s in matrix_instance:
                        for target, trans_p in matrix_instance[s].items():
                            next_probs[target] = next_probs.get(target, 0.0) + (p * trans_p)
                state_probs = next_probs
            return state_probs.get("(Conversion)", 0.0)

        base_prob = calculate_conversion_probability(transition_matrix)
        if base_prob == 0:
            base_prob = 1.0

        removal_effects = {}
        for ch in self.channels:
            if ch not in transition_matrix:
                removal_effects[ch] = 0.0
                continue
                
            altered_matrix = {}
            for s_from, targets in transition_matrix.items():
                if s_from == ch:
                    continue
                altered_matrix[s_from] = {}
                for s_to, p in targets.items():
                    if s_to == ch:
                        altered_matrix[s_from]["(Dropoff)"] = altered_matrix[s_from].get("(Dropoff)", 0.0) + p
                    else:
                        altered_matrix[s_from][s_to] = p
                        
            altered_prob = calculate_conversion_probability(altered_matrix)
            removal_effects[ch] = (base_prob - altered_prob) / base_prob

        total_effects = sum(removal_effects.values())
        if total_effects == 0:
            total_effects = 1.0

        total_converted_revenue = sum(j.revenue for j in self.journeys if j.converted == 1)
        for ch in self.channels:
            allocation[ch] = (removal_effects.get(ch, 0.0) / total_effects) * total_converted_revenue
            
        return allocation