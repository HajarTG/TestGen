package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;
import java.util.Optional;

/**
 * Sample UserService to demonstrate test generation.
 * Upload sample-java/ as a zip to test the pipeline.
 */
@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    public User createUser(String name, String email) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name cannot be blank");
        }
        if (email == null || !email.contains("@")) {
            throw new IllegalArgumentException("Invalid email address");
        }
        Optional<User> existing = userRepository.findByEmail(email);
        if (existing.isPresent()) {
            throw new RuntimeException("User with email already exists: " + email);
        }
        User user = new User();
        user.setName(name.trim());
        user.setEmail(email.toLowerCase());
        return userRepository.save(user);
    }

    public User getUserById(Long id) {
        if (id == null || id <= 0) {
            throw new IllegalArgumentException("Invalid user ID");
        }
        return userRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("User not found: " + id));
    }

    public List<User> searchUsers(String query) {
        if (query == null || query.isBlank()) {
            return userRepository.findAll();
        }
        String normalized = query.trim().toLowerCase();
        if (normalized.length() < 2) {
            throw new IllegalArgumentException("Search query too short");
        }
        return userRepository.findByNameContainingIgnoreCase(normalized);
    }

    public boolean deactivateUser(Long id) {
        try {
            User user = getUserById(id);
            if (!user.isActive()) {
                return false;
            }
            user.setActive(false);
            userRepository.save(user);
            return true;
        } catch (RuntimeException e) {
            System.err.println("Failed to deactivate user " + id + ": " + e.getMessage());
            return false;
        }
    }

    public int calculateUserScore(User user) {
        int score = 0;
        if (user == null) return 0;
        if (user.getEmail() != null && user.getEmail().endsWith(".edu")) {
            score += 10;
        }
        if (user.getPostCount() > 100) {
            score += 20;
        } else if (user.getPostCount() > 10) {
            score += 5;
        }
        for (String badge : user.getBadges()) {
            if ("gold".equals(badge)) score += 50;
            else if ("silver".equals(badge)) score += 25;
            else if ("bronze".equals(badge)) score += 10;
        }
        return Math.min(score, 100);
    }
}
