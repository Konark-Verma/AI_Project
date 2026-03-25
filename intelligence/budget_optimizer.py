from services.flight_service import get_flight_prices, get_accommodation_estimate
from services.location_service import get_currency_rate
from services.train_service import get_train_info

def optimize_budget(
    budget,
    travelers,
    days,
    source="",
    destination="",
    transport=None,
    distance_km=None,
    travel_type="city",
):
    """Optimize travel budget with strict cap enforcement (in INR).
    
    Args:
        budget (float): total maximum budget in INR (STRICT CAP)
        travelers (int): number of travelers
        days (int): trip duration in days
        source (str): source city for flight pricing
        destination (str): destination city for flight pricing
        transport (str|None): recommended transport mode (Flight/Train/Bus/Cab)
        distance_km (float|None): route distance for non-flight estimates
        travel_type (str): 'city' or 'international'
    
    Returns:
        str: formatted budget breakdown with strict cap enforcement
    """
    try:
        per_person = budget / travelers
        per_day = budget / days
        
        mode = "Flight" if travel_type == "international" else (transport or "Flight")

        def _parse_first_rupee_amount(s: str) -> float:
            # Extract the first "₹12,345" (or similar) amount in a string.
            if not isinstance(s, str):
                return 0.0
            if "₹" not in s:
                return 0.0
            part = s.split("₹", 1)[1]
            num = []
            for ch in part:
                if ch.isdigit() or ch == ",":
                    num.append(ch)
                else:
                    break
            try:
                return float("".join(num).replace(",", ""))
            except Exception:
                return 0.0

        # Get real pricing from APIs (or lightweight estimates)
        if source and destination:
            transport_cost = 0.0
            transport_label = "Transport"
            if mode == "Flight":
                flights = get_flight_prices(source, destination, days=7)
                transport_label = "Flights"
                if isinstance(flights.get("price"), str):
                    price_str = flights["price"].replace("₹", "").replace(",", "").split("-")[0]
                    try:
                        transport_cost = float(price_str) * travelers
                    except Exception:
                        transport_cost = 41500 * travelers
            elif mode == "Train" and distance_km is not None:
                train = get_train_info(source, destination, distance_km, travelers)
                transport_label = "Train"
                # train["price"] already includes travelers; take low-end estimate
                transport_cost = _parse_first_rupee_amount(train.get("price", "")) or (1200 * travelers)
            else:
                # For Cab/Bus or unknown: reserve a reasonable transport slice
                transport_label = f"Transport ({mode})" if mode else "Transport"
                transport_cost = budget * 0.12
            
            accommodation = get_accommodation_estimate(destination, days)
            accommodation_cost = 0
            if isinstance(accommodation.get("total_for_stay"), str):
                cost_str = accommodation["total_for_stay"].replace("₹", "").replace("~", "").replace(",", "")
                try:
                    accommodation_cost = float(cost_str) * travelers
                except:
                    accommodation_cost = 6640 * days * travelers
            
            # STRICT CAP ENFORCEMENT: Adjust allocations if necessary
            total_fixed_costs = transport_cost + accommodation_cost
            
            if total_fixed_costs > budget * 0.85:  # If fixed costs exceed 85% of budget
                # Reduce accommodation to ensure budget cap
                accommodation_cost = budget * 0.4  # Cap accommodation at 40% of budget
                transport_cost = min(transport_cost, budget * (0.35 if mode == "Flight" else 0.25))
            
            # Remaining for food, transport, activities
            remaining = budget - transport_cost - accommodation_cost
            other_costs = max(remaining, 0)  # Can't be negative
            
            # FINAL VERIFICATION: Ensure total never exceeds budget
            actual_total = transport_cost + accommodation_cost + other_costs
            if actual_total > budget:
                # Scale everything down proportionally
                scale_factor = budget / actual_total
                transport_cost *= scale_factor
                accommodation_cost *= scale_factor
                other_costs *= scale_factor
            
            breakdown = f"""Budget Breakdown (₹{budget:,.0f}):
├─ {transport_label}: ₹{transport_cost:,.0f} ({travelers} travelers)
├─ Accommodation: ₹{accommodation_cost:,.0f} ({days} days)
├─ Food & Activities: ₹{other_costs:,.0f}
├─ Per day: ₹{per_day:,.0f}
└─ Per person per day: ₹{per_person/days:,.0f}

Budget Type: {'Luxury' if per_day > 41500 else 'Standard' if per_day > 8300 else 'Budget'}
✓ Total: ₹{actual_total:,.0f} """
            return breakdown
    except Exception as e:
        print(f"Budget optimization error: {e}")
    
    # Fallback to simple breakdown (in INR)
    per_day = budget / days
    per_person = budget / travelers
    
    breakdown = f"""Budget Breakdown (₹{budget:,.0f}):
├─ Per day: ₹{per_day:,.0f}
├─ Per person: ₹{per_person:,.0f}
└─ Total for {days} days, {travelers} travelers

Budget Type: {'Luxury' if per_day > 41500 else 'Standard' if per_day > 8300 else 'Budget'}
✓ Total will not exceed ₹{budget:,.0f}"""
    
    return breakdown