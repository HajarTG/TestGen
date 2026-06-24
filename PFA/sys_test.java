package com.example.demo.service;

import java.util.List;

public class SystemManager {

    public double calculateTotal(List<Double> prices, double discountPercent) {
        if (prices == null || prices.isEmpty()) {
            throw new IllegalArgumentException("Prices list cannot be empty");
        }
        if (discountPercent < 0 || discountPercent > 100) {
            throw new IllegalArgumentException("Discount must be between 0 and 100");
        }

        double total = 0;
        for (double price : prices) {
            if (price < 0) throw new IllegalArgumentException("Price cannot be negative");
            total += price;
        }

        double discount = total * (discountPercent / 100);
        return total - discount;
    }

    public String getOrderStatus(int statusCode) {
        switch (statusCode) {
            case 1: return "PENDING";
            case 2: return "CONFIRMED";
            case 3: return "SHIPPED";
            case 4: return "DELIVERED";
            default: return "UNKNOWN";
        }
    }

    public boolean isEligibleForFreeShipping(double orderTotal, boolean isPremiumUser) {
        if (isPremiumUser) return true;
        return orderTotal >= 50.0;
    }
}
