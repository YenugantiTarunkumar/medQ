import datetime

class InventoryPredictionEngine:
    def predict_demand_and_shortage(self, medicine):
        """
        Calculates projected 7-day demand and shortage risk based on current quantity & min stock.
        """
        current_qty = medicine.quantity
        min_stock = medicine.min_stock
        
        # Estimate average daily consumption rate
        # Demo formula: Base 5-15 units per day depending on category
        category = medicine.category
        if category in ['Analgesic', 'Antibiotic', 'Anti-inflammatory']:
            daily_burn_rate = 15
        elif category in ['Diabetes']:
            daily_burn_rate = 8
        else:
            daily_burn_rate = 5

        projected_7day_demand = daily_burn_rate * 7
        predicted_remaining_7day = current_qty - projected_7day_demand

        if predicted_remaining_7day < 0:
            shortage_amount = abs(predicted_remaining_7day)
            risk_level = 'HIGH'
            alert_message = f"CRITICAL DEMAND SHORTAGE PREDICTED: Projected 7-day demand ({projected_7day_demand} units) exceeds current stock ({current_qty} units). Estimated deficit: {shortage_amount} units."
        elif predicted_remaining_7day < min_stock:
            shortage_amount = min_stock - predicted_remaining_7day
            risk_level = 'MODERATE'
            alert_message = f"LOW STOCK WARNING PREDICTED: Stock projected to drop below minimum threshold ({min_stock} units) within 7 days."
        else:
            shortage_amount = 0
            risk_level = 'LOW'
            alert_message = "Stock levels are healthy for projected 7-day demand."

        return {
            'medicine_id': medicine.id,
            'medicine_name': medicine.name,
            'current_quantity': current_qty,
            'min_stock': min_stock,
            'daily_burn_rate': daily_burn_rate,
            'projected_7day_demand': projected_7day_demand,
            'predicted_remaining_7day': max(0, predicted_remaining_7day),
            'shortage_amount': shortage_amount,
            'risk_level': risk_level,
            'alert_message': alert_message
        }

inventory_engine = InventoryPredictionEngine()
