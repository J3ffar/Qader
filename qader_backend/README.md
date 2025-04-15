*   [1. Authentication](#authentication)
*   [2. User Profile & Settings](#user-profile--settings)
*   [3. Public Content](#public-content)
*   [4. Learning Content](#learning-content)
*   [5. Study & Progress](#study--progress)
*   [6. Blog](#blog)
*   [7. Gamification](#gamification)
*   [8. Challenges](#challenges)
*   [9. Student Community](#student-community)
*   [10. Admin Support](#admin-support)
*   [11. Admin Panel](#admin-panel)

**Assumptions:**

1.  **Authentication:** JWT (JSON Web Tokens). Requests to protected endpoints require an `Authorization: Bearer <access_token>` header.
2.  **Permissions:** Standard DRF permissions (`AllowAny`, `IsAuthenticated`) and custom permissions (`IsSubscribed`, `IsAdmin`, `IsOwnerOrAdmin`, `IsSubAdminWithPermission`) will be used as needed. `IsSubscribed` checks if the user has an active subscription (e.g., `UserProfile.subscription_expires_at > now()`).
3.  **Base URL:** All API endpoints are prefixed with `/api/v1/`.
4.  **Response Format:** Consistent JSON responses. Success responses will generally include requested data or a success message. Error responses will use DRF's default structured format (e.g., `{"field_name": ["Error message."], "non_field_errors": ["General error."]}`) with appropriate HTTP status codes (400, 401, 403, 404, 500, etc.).
5.  **Versioning:** Using URL Path Versioning (`/api/v1/`).
6.  **Data Transfer Objects:** Serializers define the structure for request validation and response formatting. JSON examples reflect the expected serialized data.
7.  **Pagination:** List endpoints (e.g., `GET /learning/questions/`, `GET /study/tests/`) use page number pagination by default. Responses for paginated lists will have the following structure:
    ```json
    {
      "count": 150, // Total number of items across all pages
      "next": "https://domain.com/api/v1/app/?page=2", // URL for the next page (or null)
      "previous": null, // URL for the previous page (or null)
      "results": [
        // Array of objects for the current page
        { ... },
        { ... }
      ]
    }
    ```
    Pagination is controlled via `page` (integer, page number) and `page_size` (integer, items per page) query parameters. The default `page_size` is 20, but can be overridden by the client if configured on the backend.

---

**API Endpoint Documentation (v1)**

**1. Authentication (`/api/v1/auth/`)**
<a name="authentication"></a>
*   **`POST /register/`**
    *   **Action:** Register a new student user and activate subscription via serial code.
    *   **Permissions:** `AllowAny`
    *   **Request Body:**
        ```json
        {
          "full_name": "Ali Ahmed Mohamed",
          "gender": "male", // "male", "female", "other", "prefer_not_say"
          "preferred_name": "Ali",
          "grade": "Grade 12",
          "has_taken_qiyas_before": true,
          "username": "ali_student99", // Identifier
          "email": "ali.ahmed@example.com",
          "serial_code": "QADER-XYZ123-ABC",
          "password": "VeryStrongPassword123!",
          "password_confirm": "VeryStrongPassword123!"
        }
        ```
    *   **Success Response (201 Created):** Returns user info and tokens.
        ```json
        {
          "user": {
            "id": 15,
            "username": "ali_student99",
            "email": "ali.ahmed@example.com",
            "full_name": "Ali Ahmed Mohamed",
            "preferred_name": "Ali",
            "role": "student",
            "subscription_active": true, // Calculated based on serial code
            "subscription_expires_at": "2024-10-21T10:00:00Z" // Example expiry
          },
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // Access Token
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // Refresh Token
        }
        ```
    *   **Error Response (400 Bad Request):** If validation fails (e.g., passwords mismatch, email/username exists, invalid/used serial code).
        ```json
        {
          "email": ["user with this email already exists."],
          "serial_code": ["Invalid or already used serial code."],
          "password_confirm": ["Passwords do not match."]
        }
        ```

*   **`POST /login/`**
    *   **Action:** Authenticate a user and return tokens.
    *   **Permissions:** `AllowAny`
    *   **Request Body:**
        ```json
        {
          "username": "ali_student99", // Identifier
          "password": "VeryStrongPassword123!"
          // "remember_me" is handled client-side by storing the refresh token longer
        }
        ```
    *   **Success Response (200 OK):**
        ```json
        {
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "user": { // Optional: Include basic info to avoid immediate /me call
            "id": 15,
            "username": "ali_student99",
            "preferred_name": "Ali",
            "role": "student",
            "subscription_active": true,
            "profile_picture_url": "/media/profiles/ali_pic.jpg", // Example path
             "level_determined": true // Boolean indicating if level assessment was done
          }
        }
        ```
    *   **Error Response (401 Unauthorized):** If credentials are invalid.
        ```json
        {
          "detail": "No active account found with the given credentials"
        }
        ```

*   **`POST /logout/`**
    *   **Action:** Invalidate the refresh token (if using simplejwt blacklist app). Client should discard both tokens.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:**
        ```json
        {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // Send the refresh token to blacklist
        }
        ```
    *   **Success Response (200 OK / 204 No Content):**
        ```json
        // Can be empty 204 or a simple message
        { "detail": "Logout successful." }
        ```

*   **`POST /token/refresh/`**
    *   **Action:** Obtain a new access token using a valid refresh token.
    *   **Permissions:** `AllowAny`
    *   **Request Body:**
        ```json
        {
          "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        ```
    *   **Success Response (200 OK):**
        ```json
        {
          "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // New access token
        }
        ```
    *   **Error Response (401 Unauthorized):** If refresh token is invalid or blacklisted.
        ```json
        {
            "detail": "Token is invalid or expired",
            "code": "token_not_valid"
        }
        ```

*   **`POST /password/reset/`**
    *   **Action:** Request a password reset email.
    *   **Permissions:** `AllowAny`
    *   **Request Body:**
        ```json
        {
          "email": "user@example.com" // Can also accept 'username' based on backend implementation
        }
        ```
    *   **Success Response (200 OK):** (Generic message for security)
        ```json
        {
          "detail": "If an account with this email exists, a password reset link has been sent."
        }
        ```

*   **`POST /password/reset/confirm/`**
    *   **Action:** Set a new password using the token from the reset email.
    *   **Permissions:** `AllowAny`
    *   **Request Body:** (Structure depends on the library used, e.g., `django-rest-passwordreset` or `djoser`)
        ```json
        {
          // Example for django-rest-passwordreset
          "token": "a1b2c3d4e5f6...",
          "password": "NewSecurePassword123!",
          "password_confirm": "NewSecurePassword123!"
          // Example for djoser
          // "uid": "...",
          // "token": "...",
          // "new_password": "...",
          // "re_new_password": "..."
        }
        ```
    *   **Success Response (200 OK):**
        ```json
        { "detail": "Password has been reset successfully." }
        ```
    *   **Error Response (400 Bad Request):** If token is invalid/expired or passwords don't match.
        ```json
        { "token": ["Invalid token."] }
        ```

---

**2. User Profile & Settings (`/api/v1/users/`)**
<a name="user-profile--settings"></a>

*   **`GET /me/`**
    *   **Action:** Retrieve the profile and settings of the currently logged-in user.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:** None
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 15,
          "username": "ali_student99",
          "email": "ali.ahmed@example.com",
          "full_name": "Ali Ahmed Mohamed",
          "preferred_name": "Ali",
          "gender": "male",
          "grade": "Grade 12",
          "has_taken_qiyas_before": true,
          "profile_picture_url": "/media/profiles/ali_pic.jpg", // Nullable
          "role": "student",
          "points": 1250,
          "current_streak_days": 7,
          "longest_streak_days": 15,
          "last_study_activity_at": "2024-07-20T14:30:00Z", // Nullable
          "current_level_verbal": 85.5, // Nullable (null if not assessed)
          "current_level_quantitative": 78.0, // Nullable
          "level_determined": true, // Boolean shortcut derived from levels
          "last_visited_study_option": "traditional-learning", // Slug, Nullable
          "dark_mode_preference": "dark", // "light", "dark", "system"
          "dark_mode_auto_enabled": false,
          "dark_mode_auto_time_start": null,
          "dark_mode_auto_time_end": null,
          "notify_reminders_enabled": true,
          "upcoming_test_date": "2024-09-15", // Nullable
          "study_reminder_time": "19:00:00", // Nullable
          "date_joined": "2024-07-01T10:00:00Z",
          "subscription": {
             "is_active": true,
             "expires_at": "2024-10-21T10:00:00Z" // Nullable
          },
           "referral": {
              "code": "ALI-REF-7G3K", // Nullable
              "referrals_count": 3,
              "earned_free_days": 9 // Calculated
           }
        }
        ```

*   **`PATCH /me/`**
    *   **Action:** Partially update the logged-in user's profile/settings.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:** Send only the fields to be updated.
        ```json
        {
          "preferred_name": "Ali A.",
          "grade": "University Freshman",
          "dark_mode_preference": "system",
          "notify_reminders_enabled": false,
          "upcoming_test_date": "2024-10-01",
          "study_reminder_time": "20:00:00"
          // To remove a nullable field, send null: "upcoming_test_date": null
        }
        ```
    *   **Success Response (200 OK):** Returns the full updated user profile (same structure as `GET /me/`).
    *   **Notes:** For `profile_picture`, this would likely be a separate `POST` endpoint using `multipart/form-data`. E.g., `POST /me/upload-picture/`.

*   **`POST /me/change-password/`**
    *   **Action:** Change the logged-in user's password.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:**
        ```json
        {
          "current_password": "OldSecurePassword123!",
          "new_password": "EvenNewerSecurePassword456!",
          "new_password_confirm": "EvenNewerSecurePassword456!"
        }
        ```
    *   **Success Response (200 OK):**
        ```json
        { "detail": "Password updated successfully." }
        ```
    *   **Error Response (400 Bad Request):** If current password is wrong or new passwords don't match.
        ```json
        { "current_password": ["Invalid password."] }
        ```

---

**3. Public Content (`/api/v1/content/`)**
<a name="public-content"></a>

*   **`GET /pages/{slug}/`**
    *   **Action:** Retrieve content for a static page (e.g., terms, story).
    *   **Permissions:** `AllowAny`
    *   **URL Parameter:** `slug` (e.g., `terms-and-conditions`, `our-story`)
    *   **Success Response (200 OK):**
        ```json
        {
          "slug": "terms-and-conditions",
          "title": "Terms and Conditions",
          "content": "<p>Welcome to Qader...</p><h2>Privacy Policy</h2>...", // HTML or Markdown
          "icon_class": null, // Optional icon info if used
          "updated_at": "2024-07-15T12:00:00Z"
        }
        ```
    *   **Error Response (404 Not Found):** If slug doesn't exist.

*   **`GET /homepage/`**
    *   **Action:** Retrieve aggregated data needed to render the homepage.
    *   **Permissions:** `AllowAny`
    *   **Success Response (200 OK):**
        ```json
        {
          "intro": { // From Page model with slug 'homepage-intro'
            "title": "Unlock Your Potential",
            "content": "Brief, motivating description..."
          },
          "praise": { // From Page model with slug 'homepage-praise' or hardcoded
            "text": "Dr. Tony recommends Qader..."
          },
          "intro_video_url": "https://youtube.com/watch?v=xyz", // From settings/config
          "features": [ // From HomepageFeatureCard model
            { "title": "Personalized Learning", "text": "Adapts to you.", "svg_image": "<svg>...</svg>" },
            { "title": "Expert Questions", "text": "High quality.", "svg_image": "<svg>...</svg>" }
          ],
          "statistics": [ // From HomepageStatistic model
            { "label": "Number of Questions", "value": "15,000+" },
            { "label": "Expected Improvement", "value": "Up to 20%" }
          ]
        }
        ```

*   **`GET /faq/`**
    *   **Action:** Retrieve all FAQ categories and their items.
    *   **Permissions:** `AllowAny`
    *   **Query Parameter:** `search` (optional string to filter questions/answers)
    *   **Success Response (200 OK):**
        ```json
        {
          "categories": [
            {
              "id": 1,
              "name": "General",
              "items": [
                { "id": 10, "question": "What is Qader?", "answer": "Qader is a platform..." },
                { "id": 11, "question": "How do I subscribe?", "answer": "You need a serial code..." }
              ]
            },
            {
              "id": 2,
              "name": "Technical",
              "items": [
                { "id": 20, "question": "I forgot my password.", "answer": "Use the 'Forgot Password' link..." }
              ]
            }
            // ... other categories
          ]
        }
        ```

*   **`GET /partners/`**
    *   **Action:** Retrieve success partner categories.
    *   **Permissions:** `AllowAny`
    *   **Success Response (200 OK):**
        ```json
        {
           "partner_categories": [
              {
                 "id": 1,
                 "name": "School Partnerships",
                 "description": "Collaborate with us to support your students.",
                 "icon_svg_or_class": "icon-school",
                 "google_form_link": "https://forms.gle/schoolpartnership"
              },
              {
                 "id": 2,
                 "name": "Course Partnerships",
                 "description": "Integrate Qader into your training programs.",
                 "icon_svg_or_class": "icon-trainer",
                 "google_form_link": "https://forms.gle/coursepartnership"
              },
              {
                 "id": 3,
                 "name": "Student Partnerships",
                 "description": "Become an ambassador for Qader.",
                 "icon_svg_or_class": "icon-student",
                 "google_form_link": "https://forms.gle/studentpartnership"
              }
           ],
           "why_partner_text": { // From Page model with slug 'why-partner' or similar
              "title": "Why Partner With Us?",
              "content": "Beautiful design and appropriate explanation..."
           }
        }
        ```

*   **`POST /contact-us/`**
    *   **Action:** Submit a message from the Contact Us form.
    *   **Permissions:** `AllowAny`
    *   **Request Body:** `multipart/form-data` if allowing attachments.
        *   `full_name`: "Fatima Hassan"
        *   `email`: "fatima@example.com"
        *   `subject`: "Inquiry about Partnership"
        *   `message`: "Detailed message here..."
        *   `attachment`: (optional file data)
    *   **Success Response (201 Created):**
        ```json
        {
          "detail": "Thank you for contacting us. We will get back to you as soon as possible."
        }
        ```
    *   **Error Response (400 Bad Request):** For validation errors.
        ```json
        { "email": ["Enter a valid email address."] }
        ```

---

**4. Learning Content (`/api/v1/learning/`)**
<a name="learning-content"></a>

*   **`GET /sections/`**
    *   **Action:** List main learning sections (Verbal, Quantitative) with pagination.
    *   **Permissions:** `IsAuthenticated`
    *   **Query Parameters:**
        *   `page` (integer): Page number.
        *   `page_size` (integer): Number of items per page.
        *   `ordering` (string): Field to order by (e.g., `order`, `name`, `-order`).
    *   **Success Response (200 OK):**
        ```json
        {
          "count": 2, // Total number of sections
          "next": null, // URL for the next page (or null)
          "previous": null, // URL for the previous page (or null)
          "results": [
            { "id": 1, "name": "Verbal Section", "slug": "verbal", "description": "...", "order": 1 },
            { "id": 2, "name": "Quantitative Section", "slug": "quantitative", "description": "...", "order": 2 }
          ]
        }
        ```

*   **`GET /sections/{section_slug}/subsections/`**
    *   **Action:** List subsections within a specific section with pagination.
    *   **Permissions:** `IsAuthenticated`
    *   **Query Parameters:**
        *   `page` (integer): Page number.
        *   `page_size` (integer): Number of items per page.
        *   `ordering` (string): Field to order by (e.g., `order`, `name`).
        *   *(Implicit Filter: URL path contains `section_slug`)*
    *   **Success Response (200 OK):** (Example for `quantitative`)
        ```json
        {
           "count": 5, // Total number of subsections in this section
           "next": "/api/v1/learning/sections/quantitative/subsections/?page=2",
           "previous": null,
           "results": [
             { "id": 10, "name": "Algebra Problems", "slug": "algebra-problems", "description": "...", "order": 1 },
             { "id": 11, "name": "Engineering Problems", "slug": "engineering-problems", "description": "...", "order": 2 },
             { "id": 12, "name": "Arithmetic Problems", "slug": "arithmetic-problems", "description": "...", "order": 3 }
             // Potentially more depending on page_size
           ]
        }
        ```

*   **`GET /subsections/{subsection_slug}/skills/`**
    *   **Action:** List skills within a specific subsection with pagination.
    *   **Permissions:** `IsAuthenticated`
    *   **Query Parameters:**
        *   `page` (integer): Page number.
        *   `page_size` (integer): Number of items per page.
        *   `search` (string): Search term for skill name or description.
        *   `ordering` (string): Field to order by (e.g., `name`).
        *   *(Implicit Filter: URL path contains `subsection_slug`)*
    *   **Success Response (200 OK):** (Example for `algebra-problems`)
        ```json
        {
          "count": 8, // Total number of skills in this subsection
          "next": null,
          "previous": null,
          "results": [
             { "id": 101, "name": "Solving Linear Equations", "slug": "solving-linear-equations", "description": "..." },
             { "id": 102, "name": "Factoring Quadratics", "slug": "factoring-quadratics", "description": "..." }
             // ... other skills in this subsection up to page_size
          ]
        }
        ```

*   **`GET /questions/`**
    *   **Action:** Retrieve questions based on filters with pagination.
    *   **Permissions:** `IsSubscribed`
    *   **Query Parameters:**
        *   `page` (integer): Page number.
        *   `page_size` (integer): Number of items per page.
        *   `subsection__slug` (string): Filter by subsection slug (exact match or `in` for multiple: `?subsection__slug__in=slug1,slug2`).
        *   `skill__slug` (string): Filter by skill slug (exact match or `in` for multiple).
        *   `starred` (boolean): Filter for questions starred by the current user (`true`/`false`).
        *   `not_mastered` (boolean): Filter for skills below a proficiency threshold (`true`) - *Requires Study App*.
        *   `difficulty` (integer): Filter by difficulty level (exact match or `in`, `gte`, `lte`).
        *   `search` (string): Search term across relevant fields.
        *   `ordering` (string): Field to order by (e.g., `difficulty`, `-id`).
        *   `exclude_ids` (string): Comma-separated list of question IDs to exclude.
    *   **Success Response (200 OK):** Returns a paginated list of questions *without* correct answers or explanations.
        ```json
        {
          "count": 150, // Total matching questions
          "next": "/api/v1/learning/questions/?page=2&difficulty=3", // Example next page URL
          "previous": null,
          "results": [
            {
              "id": 501,
              "question_text": "If 2x + 5 = 15, what is the value of x?",
              "option_a": "3",
              "option_b": "5",
              "option_c": "7",
              "option_d": "10",
              "hint": "Isolate the term with x first.",
              "solution_method_summary": "Solve the linear equation.",
              "difficulty": 2,
              "subsection": "algebra-problems", // Using SlugRelatedField in serializer
              "skill": "solving-linear-equations", // Using SlugRelatedField in serializer
              "is_starred": true
            },
            {
              "id": 508,
              "question_text": "What is the area of a circle with radius 5?",
              // ... options etc ...
              "difficulty": 3,
              "subsection": "engineering-problems",
              "skill": "circle-area",
              "is_starred": false
            }
            // ... other questions up to page_size
          ]
        }
        ```

*   **`GET /questions/{question_id}/`**
    *   **Action:** Retrieve full details for a single question (e.g., for review after answering).
    *   **Permissions:** `IsSubscribed`
    *   **Success Response (200 OK):** Includes correct answer and explanation. *(No change here as it's a detail view, not a list)*
        ```json
        {
          "id": 501,
          "question_text": "If 2x + 5 = 15, what is the value of x?",
          "option_a": "3",
          "option_b": "5",
          "option_c": "7",
          "option_d": "10",
          "correct_answer": "B",
          "explanation": "<p>1. Subtract 5 from both sides: 2x = 15 - 5 = 10.</p><p>2. Divide by 2: x = 10 / 2 = 5.</p>",
          "hint": "Isolate the term with x first.",
          "solution_method_summary": "Solve the linear equation.",
          "difficulty": 2,
          // Use nested serializer for detail view
          "subsection": { "id": 10, "slug": "algebra-problems", "name": "Algebra Problems", "description": "...", "order": 1, "skills": [...] },
          "skill": { "id": 101, "slug": "solving-linear-equations", "name": "Solving Linear Equations", "description": "..." },
          "is_starred": true
        }
        ```

*   **`POST /questions/{question_id}/star/`**
    *   *(No change needed)*
    *   **Action:** Star a question for the current user.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:** None
    *   **Success Response (201 Created / 200 OK):**
        ```json
        { "status": "starred" }
        ```

*   **`DELETE /questions/{question_id}/star/`**
    *   *(No change needed)*
    *   **Action:** Unstar a question for the current user.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:** None
    *   **Success Response (200 OK):**
        ```json
        { "status": "unstarred" }
        ```

---

**5. Study & Progress (`/api/v1/study/`)**
<a name="study--progress"></a>

*   **`POST /level-assessment/start/`**
    *   **Action:** Start a level assessment test. Checks if user *needs* assessment (first login or retake).
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "sections": ["verbal", "quantitative"], // List of section slugs
          "num_questions": 30 // Default or user choice
        }
        ```
    *   **Success Response (201 Created):** Returns test attempt ID and the list of questions.
        ```json
        {
          "attempt_id": 123,
          "questions": [
            // List of question objects (structure like GET /learning/questions/ response)
            { "id": 601, "question_text": "...", "option_a": "...", ... },
            { "id": 602, "question_text": "...", "option_a": "...", ... }
            // ... 30 questions
          ]
        }
        ```
     *   **Error Response (400 Bad Request):** If level already determined and not explicitly retaking.
        ```json
        { "detail": "Level already determined. Use 'Retake Assessment' option if needed." }
        ```


*   **`POST /level-assessment/{attempt_id}/submit/`**
    *   **Action:** Submit answers for the level assessment test.
    *   **Permissions:** `IsSubscribed` & Owner of `attempt_id`.
    *   **Request Body:**
        ```json
        {
          "answers": [
            { "question_id": 601, "selected_answer": "B", "time_taken_seconds": 45 },
            { "question_id": 602, "selected_answer": "A", "time_taken_seconds": 60 }
            // ... answers for all questions in the attempt
          ]
        }
        ```
    *   **Success Response (200 OK):** Returns calculated levels and summary.
        ```json
        {
          "attempt_id": 123,
          "results": {
            "overall_score": 81.5,
            "verbal_score": 85.5,
            "quantitative_score": 78.0,
            "proficiency_summary": { // Breakdown per skill/subsection
              "algebra-problems": 0.8,
              "reading-comprehension": 0.9
              // ...
            },
            "message": "Your personalized learning path is now set!"
          },
          "updated_profile": { // Reflects updated levels in profile
             "current_level_verbal": 85.5,
             "current_level_quantitative": 78.0,
             "level_determined": true
          }
        }
        ```
    *   **Notes:** Backend calculates scores, updates `UserTestAttempt`, `UserProfile`, and potentially `UserSkillProficiency`. Creates `UserQuestionAttempt` records.

*   **`POST /traditional/answer/`**
    *   **Action:** Submit an answer for a single question in Traditional Learning mode.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "question_id": 501,
          "selected_answer": "B", // "A", "B", "C", "D"
          "time_taken_seconds": 30, // Optional, used for stats
          "used_hint": false,
          "used_elimination": false, // If this feature exists
          "used_solution_method": false
        }
        ```
    *   **Success Response (200 OK):** Returns correctness, correct answer, explanation, and points earned.
        ```json
        {
          "question_id": 501,
          "is_correct": true,
          "correct_answer": "B",
          "explanation": "<p>1. Subtract 5...</p>",
          "points_earned": 1,
          "current_total_points": 1251,
          "streak_updated": true, // Indicates if streak counter changed
          "current_streak": 8
        }
        ```
    *   **Notes:** Backend creates `UserQuestionAttempt` (mode='traditional'), updates `UserSkillProficiency`, updates `UserProfile.points` via `PointLog`, updates `UserProfile` streak.

*   **`POST /emergency-mode/start/`**
    *   **Action:** Initiate Emergency Mode, get a suggested plan.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "reason": "Feeling overwhelmed before the test.", // Optional
          "available_time_hours": 2, // Optional, influences plan
          "focus_areas": ["quantitative"] // Optional list of section slugs to prioritize
        }
        ```
    *   **Success Response (201 Created):** Returns session ID and the plan.
        ```json
        {
          "session_id": 45,
          "suggested_plan": {
            "focus_skills": [ // List of skill slugs identified as weak
              "factoring-quadratics",
              "data-analysis-graphs"
            ],
            "recommended_questions": 15, // Suggested number based on time/weakness
            "quick_review_topics": ["Linear equations formula", "Common geometry shapes"]
          },
          "tips": [ // General tips
            "Take deep breaths before starting.",
            "Focus on understanding, not just speed right now."
          ]
        }
        ```
    *   **Notes:** Backend creates `EmergencyModeSession`, analyzes `UserSkillProficiency` (or test history) to generate the plan.

*   **`PATCH /emergency-mode/{session_id}/`**
    *   **Action:** Update settings for an active Emergency Mode session.
    *   **Permissions:** `IsSubscribed` & Owner of `session_id`.
    *   **Request Body:**
        ```json
        {
          "calm_mode_active": true, // Activate/deactivate calm visual/audio settings
          "shared_with_admin": true // Share status with admin (creates notification/flag)
        }
        ```
    *   **Success Response (200 OK):** Returns the updated session status.
        ```json
        {
          "session_id": 45,
          "calm_mode_active": true,
          "shared_with_admin": true
          // ... other session details
        }
        ```

*   **`GET /emergency-mode/questions/`** (Implementation Detail: Often combined with POST answer)
    *   **Action:** Get the next question based on the emergency plan.
    *   **Permissions:** `IsSubscribed` & Owner of active `session_id`.
    *   **Query Parameters:** `session_id`
    *   **Success Response (200 OK):** Returns a single question object (structure like GET `/learning/questions/` but focused on weak areas from the plan). *Note: Often, the frontend fetches a batch via `/learning/questions/?skill=...` based on the plan, rather than one-by-one.*

*   **`POST /emergency-mode/answer/`**
    *   **Action:** Submit an answer in Emergency Mode.
    *   **Permissions:** `IsSubscribed` & Owner of active `session_id`.
    *   **Request Body:**
        ```json
        {
          "question_id": 701,
          "selected_answer": "C",
          "session_id": 45
          // No timer/hint data needed if Calm Mode is active
        }
        ```
    *   **Success Response (200 OK):** Returns correctness and explanation.
        ```json
        {
          "question_id": 701,
          "is_correct": false,
          "correct_answer": "D",
          "explanation": "...",
          "points_earned": 0 // Or maybe partial points for trying
        }
        ```
    *   **Notes:** Creates `UserQuestionAttempt` (mode='emergency'), updates proficiency.

*   **`POST /conversation/start/`**
    *   **Action:** Start a new conversational learning session.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "ai_tone": "cheerful" // Optional: "cheerful", "serious"
        }
        ```
    *   **Success Response (201 Created):** Returns session ID and initial AI message.
        ```json
        {
          "session_id": 55,
          "initial_message": "Hey there! Ready to tackle some tricky concepts? 😎 What's on your mind?",
          "ai_tone": "cheerful"
        }
        ```
    *   **Notes:** Creates `ConversationSession`. Backend might identify a weak area to start with.

*   **`POST /conversation/{session_id}/message/`**
    *   **Action:** Send a user message or action ("Got it") to the AI.
    *   **Permissions:** `IsSubscribed` & Owner of `session_id`.
    *   **Request Body (User Query):**
        ```json
        {
          "message": "Can you explain contextual errors again?",
          "context_question_id": null // Optional ID if asking about a specific question
        }
        ```
    *   **Request Body (User Understood):**
        ```json
        {
          "action": "understood",
          "context_question_id": 805 // ID of the question the AI just explained/tested
        }
        ```
    *   **Success Response (200 OK - AI Reply):**
        ```json
        {
          "session_id": 55,
          "ai_response": "Sure thing! Contextual errors are all about finding the word that doesn't fit the sentence's meaning...",
          "follow_up_question": null // AI might pose a direct question here
        }
        ```
    *   **Success Response (200 OK - AI Test after "Got it"):**
        ```json
        {
          "session_id": 55,
          "ai_response": "Great! Let's test that. Look at this sentence: ... Which word is the contextual error?",
          "test_question": { // A mini-question object
             "id": 806, // This is a Qader question ID used for tracking
             "text": "The diligent student always procrastinates on his homework.",
             "options": ["diligent", "procrastinates", "homework"] // Simplified for conversation
          }
        }
        ```
    *   **Notes:** Backend interacts with ChatGPT API, updates `ConversationSession.chat_log`. If `action: understood`, backend might fetch a relevant `Question`, format it for conversation, and return it. If user answers the test_question in a subsequent message, backend validates, creates `UserQuestionAttempt` (mode='conversation'), and informs the AI of the result for the next conversational turn.

*   **`GET /tests/`**
    *   **Action:** List the user's previous test attempts.
    *   **Permissions:** `IsSubscribed`
    *   **Query Parameters:** `page`, `page_size`
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
          "count": 5,
          "next": null,
          "previous": null,
          "results": [
            {
              "attempt_id": 123,
              "test_type": "Level Assessment", // Derived from type/config
              "date": "2024-07-21T10:30:00Z", // Start time
              "num_questions": 30, // Calculated from linked attempts
              "score_percentage": 81.5,
              "status": "completed",
              "performance": { // Summary
                "verbal": 85.5,
                "quantitative": 78.0
              }
            },
            {
              "attempt_id": 110,
              "test_type": "Algebra Practice",
              "date": "2024-07-18T15:00:00Z",
              "num_questions": 10,
              "score_percentage": 90.0,
              "status": "completed",
               "performance": { "quantitative": 90.0 }
            }
            // ... other attempts
          ]
        }
        ```

*   **`POST /tests/start/`**
    *   **Action:** Start a new test (practice, simulation, custom).
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "test_type": "custom", // "practice", "simulation", "custom"
          "config": { // Define the test parameters
            "name": "My Quant Practice", // Optional name for custom test
            "subsections": ["algebra-problems", "arithmetic-problems"], // List of slugs/ids
            "skills": [], // Optional list of specific skill slugs/ids
            "num_questions": 20,
            "starred": false, // Include only starred questions?
            "not_mastered": true, // Include questions from weak areas?
             "full_simulation": false // Is this a full timed simulation?
          }
        }
        ```
    *   **Success Response (201 Created):** Returns attempt ID and questions.
        ```json
        {
          "attempt_id": 124,
          "questions": [
            // List of 20 question objects based on config
            { "id": 901, "question_text": "...", ... },
            { "id": 902, "question_text": "...", ... }
          ]
        }
        ```
    *   **Notes:** Backend creates `UserTestAttempt`, generates/selects questions based on the config, potentially applying logic for `not_mastered`.

*   **`GET /tests/{attempt_id}/`**
    *   **Action:** Retrieve details of a specific test attempt (ongoing or completed).
    *   **Permissions:** `IsSubscribed` & Owner of `attempt_id`.
    *   **Success Response (200 OK):**
        ```json
        {
          "attempt_id": 124,
          "test_type": "Custom",
          "config_name": "My Quant Practice",
          "date": "2024-07-22T11:00:00Z",
          "num_questions": 20,
          "score_percentage": null, // If ongoing or not yet submitted
          "status": "started", // "started", "completed", "abandoned"
          "questions": [ // Questions for the test
             { "id": 901, ... }, // Structure like GET /learning/questions/
             { "id": 902, ... }
             // If completed, might include user's selected answer here too
          ],
           "results_summary": null // Populated on completion
        }
        ```

*   **`POST /tests/{attempt_id}/submit/`**
    *   **Action:** Submit answers for a practice/simulation/custom test.
    *   **Permissions:** `IsSubscribed` & Owner of `attempt_id`.
    *   **Request Body:**
        ```json
        {
          "answers": [
            { "question_id": 901, "selected_answer": "A", "time_taken_seconds": 55 },
            { "question_id": 902, "selected_answer": "D", "time_taken_seconds": 70 }
            // ... answers for all questions
          ]
        }
        ```
    *   **Success Response (200 OK):** Returns final results and smart analysis.
        ```json
        {
          "attempt_id": 124,
          "status": "completed",
          "score_percentage": 85.0,
          "score_verbal": null, // If test was only quant
          "score_quantitative": 85.0,
          "results_summary": { // Detailed breakdown
            "algebra-problems": { "correct": 8, "total": 10, "score": 80.0 },
            "arithmetic-problems": { "correct": 9, "total": 10, "score": 90.0 }
          },
          "smart_analysis": "Great work on Arithmetic! Keep practicing those Algebra concepts.",
          "points_earned": 10, // Points for completing a test
           "current_total_points": 1261
        }
        ```
    *   **Notes:** Backend creates `UserQuestionAttempt` records (mode='test'), updates `UserTestAttempt`, calculates scores, updates `UserSkillProficiency`, awards points (`PointLog`), updates streak.

*   **`GET /tests/{attempt_id}/review/`**
    *   **Action:** Get detailed question-by-question review for a completed test.
    *   **Permissions:** `IsSubscribed` & Owner of `attempt_id`.
    *   **Query Parameters:** `incorrect_only=true` (optional boolean)
    *   **Success Response (200 OK):**
        ```json
        {
          "attempt_id": 124,
          "review_questions": [
            {
              "id": 901,
              "question_text": "...",
              "option_a": "...", // ... options
              "correct_answer": "A",
              "explanation": "...",
              "user_selected_answer": "A",
              "is_correct": true,
              "subsection": { "slug": "algebra-problems", "name": "Algebra Problems"},
               "skill": { "slug": "solving-linear-equations", "name": "Solving Linear Equations"}
            },
            { // Example of incorrect answer
              "id": 905,
              "question_text": "...",
              "option_a": "...", // ... options
              "correct_answer": "C",
              "explanation": "...",
              "user_selected_answer": "B",
              "is_correct": false,
               "subsection": { "slug": "algebra-problems", "name": "Algebra Problems"},
               "skill": { "slug": "factoring-quadratics", "name": "Factoring Quadratics"}
            }
            // ... other questions (potentially filtered)
          ]
        }
        ```

*   **`POST /tests/{attempt_id}/retake-similar/`**
    *   **Action:** Start a new test instance with the same configuration as a previous one.
    *   **Permissions:** `IsSubscribed` & Owner of `attempt_id`.
    *   **Request Body:** None
    *   **Success Response (201 Created):** Returns new attempt ID and new set of questions.
        ```json
        {
          "new_attempt_id": 125,
          "message": "New test started based on the configuration of attempt #124.",
          "questions": [
            // New list of question objects matching the original config
            { "id": 1001, "question_text": "...", ... }
          ]
        }
        ```
    *   **Notes:** Backend reads `UserTestAttempt.test_configuration` from the old attempt, creates a new `UserTestAttempt`, and generates a fresh set of questions.

*   **`GET /statistics/`**
    *   **Action:** Get comprehensive progress statistics for the user.
    *   **Permissions:** `IsSubscribed`
    *   **Success Response (200 OK):** Aggregated data for charts and display.
        ```json
        {
          "overall_progress": {
             "estimated_level_verbal": 86.0, // Latest estimate
             "estimated_level_quantitative": 80.5,
             "improvement_trend_verbal": 5.0, // % point improvement over period
             "improvement_trend_quantitative": 2.5,
             "mastery_level": "Advanced" // Categorical based on levels
          },
          "performance_by_section": {
            "verbal": {
               "overall_accuracy": 88.2,
               "avg_time_per_question": 55.0 // seconds
            },
             "quantitative": {
               "overall_accuracy": 82.1,
               "avg_time_per_question": 75.3
            }
          },
          "performance_by_subsection": [ // For detailed charts/tables
            { "slug": "reading-comprehension", "name": "Reading Comprehension", "accuracy": 92.0, "attempts": 50 },
            { "slug": "algebra-problems", "name": "Algebra Problems", "accuracy": 78.5, "attempts": 80 }
            // ... other subsections user has practiced
          ],
           "skill_proficiency": [ // More granular data
             { "slug": "solving-linear-equations", "name": "Solving Linear Equations", "score": 0.85, "attempts": 40},
             { "slug": "factoring-quadratics", "name": "Factoring Quadratics", "score": 0.72, "attempts": 35}
           ],
          "test_history_summary": [ // Data for progress chart (e.g., last 10 tests)
            { "date": "2024-07-18", "score": 90.0, "type": "practice" },
            { "date": "2024-07-21", "score": 81.5, "type": "level_assessment" },
            { "date": "2024-07-22", "score": 85.0, "type": "custom" }
          ]
        }
        ```
    *   **Notes:** Requires potentially complex aggregation queries on `UserTestAttempt`, `UserQuestionAttempt`, and `UserSkillProficiency` tables. Consider caching this endpoint.

*   **`PATCH /last-visited-option/`**
    *   **Action:** Save the slug of the last viewed study section.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "last_visited_study_option": "emergency-mode" // Send the slug
        }
        ```
    *   **Success Response (200 OK):**
        ```json
        { "status": "updated" }
        ```
    *   **Notes:** Updates `UserProfile.last_visited_study_option`. Frontend calls this on navigating within the Study Page.

---

**6. Blog (`/api/v1/blog/`)** ("Coming Soon" - done in the future)
<a name="blog"></a>

*   **`GET /posts/`**
    *   **Action:** List published blog posts.
    *   **Permissions:** `IsAuthenticated` (or `AllowAny`)
    *   **Query Parameters:** `tag`, `search`, `page`, `page_size`
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
          "count": 12,
          "next": "/api/v1/blog/posts/?page=2",
          "previous": null,
          "results": [
            {
              "id": 1,
              "title": "How to Start Preparing for Qudurat",
              "slug": "how-to-start-preparing",
              "author_name": "Admin Team", // Or specific author name
              "published_at": "2024-07-20T09:00:00Z",
              "excerpt": "Getting started with your Qudurat prep can seem daunting...",
              "tags": ["getting-started", "tips"]
            }
            // ... other posts
          ]
        }
        ```

*   **`GET /posts/{slug}/`**
    *   **Action:** Get full details of a single blog post.
    *   **Permissions:** `IsAuthenticated` (or `AllowAny`)
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 1,
          "title": "How to Start Preparing for Qudurat",
          "slug": "how-to-start-preparing",
          "author": { "id": 1, "name": "Admin Team" },
          "published_at": "2024-07-20T09:00:00Z",
          "content": "<h2>Set Your Goals</h2><p>First, understand what score you're aiming for...</p>", // HTML/Markdown
          "tags": ["getting-started", "tips"],
           "updated_at": "2024-07-21T10:00:00Z"
        }
        ```

*   **`POST /advice-requests/`**
    *   **Action:** Submit a request for specific advice.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "problem_type": "Struggling with Time Management in Quant", // User selection or text
          "description": "I keep running out of time on the quantitative section, especially geometry. Any strategies?"
        }
        ```
    *   **Success Response (201 Created):**
        ```json
        {
          "request_id": 5,
          "message": "Your advice request has been submitted. We'll respond via Admin Support or a notification."
        }
        ```
    *   **Notes:** Creates `BlogAdviceRequest`. Triggers admin notification.

---

**7. Gamification (`/api/v1/gamification/`)**
<a name="gamification"></a>

*   **`GET /summary/`**
    *   **Action:** Get the user's current points and streak status.
    *   **Permissions:** `IsAuthenticated`
    *   **Success Response (200 OK):**
        ```json
        {
          "points": 1261,
          "current_streak": 8,
          "longest_streak": 15
        }
        ```

*   **`GET /badges/`**
    *   **Action:** List all available badges and which ones the user has earned.
    *   **Permissions:** `IsAuthenticated`
    *   **Success Response (200 OK):**
        ```json
        [
          {
            "id": 1,
            "name": "First Full Test",
            "slug": "first-full-test",
            "description": "Completed your first full simulation test.",
            "icon_class_or_image": "badge-icon-test",
            "criteria_description": "Complete one test marked as 'Full Simulation'.",
            "is_earned": true,
            "earned_at": "2024-07-19T11:00:00Z" // Included if earned
          },
          {
            "id": 2,
            "name": "10-Day Streak",
            "slug": "10-day-streak",
            "description": "Studied for 10 consecutive days.",
            "icon_class_or_image": "badge-icon-streak-10",
             "criteria_description": "Log in and complete at least one question or test for 10 days in a row.",
            "is_earned": false,
            "earned_at": null
          }
          // ... other badges
        ]
        ```

*   **`GET /rewards-store/`**
    *   **Action:** List items available for purchase with points.
    *   **Permissions:** `IsAuthenticated`
    *   **Success Response (200 OK):**
        ```json
        [
          {
            "id": 10,
            "name": "Exclusive Avatar Frame",
            "description": "Show off your dedication with this cool frame.",
            "item_type": "avatar", // "avatar", "theme", "material", "competition_entry"
            "cost_points": 500,
            "asset_url_or_data": "/media/rewards/avatar_frame_1.png" // Path or identifier
          },
          {
            "id": 11,
            "name": "Dark Mode Theme Variant",
            "description": "A special dark theme for focus.",
            "item_type": "theme",
            "cost_points": 300,
             "asset_url_or_data": "theme-dark-variant-1" // Identifier for client-side theme
          },
           {
            "id": 12,
            "name": "Grand Competition Entry",
            "description": "Enter the monthly grand competition.",
            "item_type": "competition_entry",
            "cost_points": 1000,
            "asset_url_or_data": null
          }
          // ... other items
        ]
        ```

*   **`POST /rewards-store/purchase/{item_id}/`**
    *   **Action:** Purchase an item from the rewards store.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:** None
    *   **Success Response (200 OK):**
        ```json
        {
          "item_id": 11,
          "item_name": "Dark Mode Theme Variant",
          "points_spent": 300,
          "remaining_points": 961,
          "message": "Purchase successful!"
        }
        ```
    *   **Error Response (400 Bad Request):** If insufficient points or item inactive.
        ```json
        { "detail": "Insufficient points to purchase this item." }
        ```
    *   **Notes:** Backend checks points, creates `UserRewardPurchase`, updates `UserProfile.points`, creates `PointLog`.

*   **`GET /point-log/`**
    *   **Action:** Get the user's history of point transactions.
    *   **Permissions:** `IsAuthenticated`
    *   **Query Parameters:** `page`, `page_size`
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
           "count": 25,
           "next": "/api/v1/gamification/point-log/?page=2",
           "previous": null,
           "results": [
             {
               "id": 105,
               "points_change": -300,
               "reason_code": "REWARD_PURCHASE",
               "description": "Purchased: Dark Mode Theme Variant",
               "timestamp": "2024-07-22T14:00:00Z"
             },
             {
               "id": 104,
               "points_change": 10,
               "reason_code": "TEST_COMPLETED",
               "description": "Completed Test: My Quant Practice (ID: 124)",
               "timestamp": "2024-07-22T11:30:00Z"
             },
             {
                "id": 103,
                "points_change": 1,
                "reason_code": "QUESTION_SOLVED",
                "description": "Solved Question #501",
                "timestamp": "2024-07-22T09:15:00Z"
             }
             // ... older entries
           ]
        }
        ```

---

**8. Challenges (`/api/v1/challenges/`)**
<a name="challenges"></a>

*   **`GET /`**
    *   **Action:** List the user's challenges (pending invites, ongoing, completed).
    *   **Permissions:** `IsSubscribed`
    *   **Query Parameters:** `status=pending/ongoing/completed`, `page`, `page_size`
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
          "count": 8,
          "next": null,
          "previous": null,
          "results": [
            { // Example: Completed challenge user won
              "id": 21,
              "challenger": { "username": "friend_user", "preferred_name": "Friend" },
              "opponent": { "username": "ali_student99", "preferred_name": "Ali" }, // Current user
              "challenge_type": "Quick Quant", // Derived from config/type
              "status": "completed",
              "winner": { "username": "ali_student99", "preferred_name": "Ali" },
              "user_score": 8, // Current user's score
              "opponent_score": 6,
              "created_at": "2024-07-21T16:00:00Z",
              "completed_at": "2024-07-21T16:10:00Z"
            },
             { // Example: Pending invite for the user
              "id": 22,
              "challenger": { "username": "another_friend", "preferred_name": "Sarah" },
              "opponent": { "username": "ali_student99", "preferred_name": "Ali" }, // Current user
              "challenge_type": "Medium Verbal",
              "status": "pending", // User needs to accept/decline
              "winner": null,
              "user_score": null,
              "opponent_score": null,
              "created_at": "2024-07-22T10:00:00Z",
              "completed_at": null
            }
            // ... other challenges
          ]
        }
        ```

*   **`POST /start/`**
    *   **Action:** Initiate a new challenge (direct invite or random).
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "opponent_username": "friend_user", // Optional: For direct invite
          "challenge_type": "quick_quant_10", // Predefined type identifier
          // OR provide custom config if allowed
          // "config": { "sections": ["quantitative"], "num_questions": 10, "time_limit": 300 }
        }
        ```
    *   **Success Response (201 Created):**
        ```json
        { // If direct invite
          "id": 23,
          "status": "pending", // Waiting for opponent
          "message": "Challenge issued to friend_user!"
        }
        // OR
        { // If random matchmaking successful immediately
           "id": 24,
           "status": "ongoing", // Found opponent, ready to start
           "opponent": { "username": "random_opponent", "preferred_name": "Gamer123" },
           "message": "Random challenge started!"
           // Include questions list here if starting immediately
           // "questions": [ { "id": 1101, ... } ]
        }
        // OR
        { // If random matchmaking, waiting for opponent
           "id": 25,
           "status": "pending_matchmaking",
           "message": "Searching for a random opponent..."
        }
        ```
    *   **Notes:** Creates `Challenge`. Sends notification for direct invite. Handles matchmaking logic for random.

*   **`GET /{challenge_id}/`**
    *   **Action:** Get details of a specific challenge (for displaying status, questions).
    *   **Permissions:** `IsSubscribed` & Participant.
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 24,
          "challenger": { "username": "ali_student99", ... },
          "opponent": { "username": "random_opponent", ... },
          "challenge_type": "Quick Quant",
          "status": "ongoing", // "pending", "ongoing", "completed", "cancelled"
          "winner": null,
          "participants": [
             { "username": "ali_student99", "is_ready": true, "score": 0 },
             { "username": "random_opponent", "is_ready": false, "score": 0 } // Waiting for opponent
          ],
          "questions": [ // Included only when status is 'ongoing' and user is participant
             { "id": 1101, "question_text": "...", ... },
             { "id": 1102, ... }
          ],
           "time_remaining": 280, // In seconds, if timed. Requires backend tracking/WebSockets.
           "created_at": "...",
           "started_at": "..." // When both players were ready
        }
        ```
    *   **Notes:** Real-time updates (opponent readiness, scores, timer) are best handled via WebSockets. This endpoint gives a snapshot.

*   **`POST /{challenge_id}/accept/`**
    *   **Action:** Accept a pending challenge invitation.
    *   **Permissions:** `IsSubscribed` & Invited Opponent.
    *   **Request Body:** None
    *   **Success Response (200 OK):** Returns updated challenge details (similar to GET /{challenge_id}/).
        ```json
        {
          "id": 22,
          "status": "accepted", // Or "ongoing" if ready to start immediately
          "message": "Challenge accepted! Waiting for both players to be ready."
          // ... other details
        }
        ```
    *   **Notes:** Updates `Challenge.status`. Notifies challenger.

*   **`POST /{challenge_id}/decline/`**
    *   **Action:** Decline a pending challenge invitation.
    *   **Permissions:** `IsSubscribed` & Invited Opponent.
    *   **Request Body:** None
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 22,
          "status": "declined",
          "message": "Challenge declined."
        }
        ```
    *   **Notes:** Updates `Challenge.status`. Notifies challenger.

*   **`POST /{challenge_id}/ready/`** (*Alternative to WebSockets*)
    *   **Action:** Signal that the user is on the challenge screen and ready to start.
    *   **Permissions:** `IsSubscribed` & Participant.
    *   **Request Body:** None
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 22,
          "user_status": "ready",
          "challenge_status": "waiting_opponent" // Or "ongoing" if opponent was already ready
        }
        ```
    *   **Notes:** Updates `ChallengeAttempt.is_ready`. Backend checks if both are ready to transition `Challenge.status` to 'ongoing'.

*   **`POST /{challenge_id}/answer/`**
    *   **Action:** Submit an answer during an ongoing challenge.
    *   **Permissions:** `IsSubscribed` & Participant in 'ongoing' challenge.
    *   **Request Body:**
        ```json
        {
          "question_id": 1101,
          "selected_answer": "C",
          "time_taken_seconds": 25 // Optional but useful for tie-breaking/stats
        }
        ```
    *   **Success Response (200 OK):** Minimal response. Frontend likely relies on WebSocket for immediate feedback/score update.
        ```json
        { "status": "answer_received" }
        // Optionally include immediate correctness if not using WebSockets
        // { "is_correct": true }
        ```
    *   **Notes:** Creates `UserQuestionAttempt` (mode='challenge'). Backend updates score in `ChallengeAttempt`. Needs logic to detect challenge end (all questions answered / time limit).

*   **`GET /{challenge_id}/results/`**
    *   **Action:** Get the final results of a completed challenge.
    *   **Permissions:** `IsSubscribed` & Participant.
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 21,
          "status": "completed",
          "winner": { "username": "ali_student99", "preferred_name": "Ali" },
          "results": [
            { "username": "ali_student99", "score": 8, "is_winner": true },
            { "username": "friend_user", "score": 6, "is_winner": false }
          ],
          "points_awarded": { // Example points
             "ali_student99": 15, // 5 for participating + 10 for winning
             "friend_user": 5
          },
          "completed_at": "2024-07-21T16:10:00Z",
          "review_available": true // Flag indicating if user can review questions
        }
        ```
    *   **Notes:** Backend calculates winner, awards points (`PointLog`), potentially awards badges.

---

**9. Student Community (`/api/v1/community/`)**
<a name="student-community"></a>

*   **`GET /posts/`**
    *   **Action:** List community posts.
    *   **Permissions:** `IsSubscribed`
    *   **Query Parameters:** `post_type=discussion/achievement/partner_search/tip`, `section_filter=verbal/quantitative`, `tag=my-tag`, `search=query`, `pinned=true`, `page`, `page_size`.
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
           "count": 35,
           "next": "/api/v1/community/posts/?page=2",
           "previous": null,
           "results": [
             {
               "id": 51,
               "author": { "username": "student_x", "preferred_name": "StudentX", "profile_picture_url": "..." },
               "post_type": "discussion",
               "title": "Confused about Analogy questions",
               "content_excerpt": "I'm really struggling to see the connection in some verbal analogy questions...", // Truncated content
               "reply_count": 5,
               "created_at": "2024-07-22T08:00:00Z",
               "tags": ["verbal", "analogy"],
               "is_pinned": false,
                "is_closed": false
             },
             {
               "id": 50,
               "author": { "username": "student_y", "preferred_name": "StudentY", "profile_picture_url": "..." },
               "post_type": "achievement",
               "title": null,
               "content_excerpt": "Just hit 90% on my Quant practice test! #FirstTimeOver90",
               "reply_count": 2,
               "created_at": "2024-07-21T18:00:00Z",
               "tags": ["achievement", "FirstTimeOver90"],
               "is_pinned": false,
               "is_closed": false
             }
             // ... other posts
           ]
        }
        ```

*   **`POST /posts/`**
    *   **Action:** Create a new community post.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "post_type": "partner_search", // "discussion", "achievement", "partner_search", "tip"
          "title": "Looking for Quant Challenge Partner (Level 80+)", // Optional
          "content": "Hey everyone, looking for someone around my level (80-85% in Quant) to do some regular challenges with. Let me know!",
          "section_filter": "quantitative", // Optional section slug
          "tags": ["challenge", "partner-search"] // Optional list of tags
        }
        ```
    *   **Success Response (201 Created):** Returns the newly created post detail.
        ```json
        { // Structure similar to GET /posts/{post_id}/ below
           "id": 52,
           "author": { "username": "current_user", ... },
           "post_type": "partner_search",
           "title": "Looking for Quant Challenge Partner (Level 80+)",
           "content": "Hey everyone...",
           "replies": [], // Starts with empty replies
           "reply_count": 0,
           // ... other fields
        }
        ```
    *   **Notes:** Backend might auto-tag achievements based on content ("#FirstTimeOver90").

*   **`GET /posts/{post_id}/`**
    *   **Action:** Get a single community post and its replies.
    *   **Permissions:** `IsSubscribed`
    *   **Query Parameters:** `page`, `page_size` (for replies)
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 51,
          "author": { "username": "student_x", "preferred_name": "StudentX", "profile_picture_url": "..." },
          "post_type": "discussion",
          "title": "Confused about Analogy questions",
          "content": "I'm really struggling to see the connection in some verbal analogy questions. For example, 'Doctor : Hospital :: Teacher : ?'. Is it always 'School' or could it be 'Classroom'?",
          "section_filter": "verbal",
          "created_at": "2024-07-22T08:00:00Z",
          "updated_at": "2024-07-22T08:00:00Z",
          "tags": ["verbal", "analogy"],
          "is_pinned": false,
          "is_closed": false,
          "reply_count": 5,
          "replies": { // Paginated replies
            "count": 5,
            "next": null,
            "previous": null,
            "results": [
              {
                "id": 101,
                "author": { "username": "helper_student", "preferred_name": "Helper", "profile_picture_url": "..." },
                "content": "Think about the primary place of work. A doctor's primary place is usually a hospital. A teacher's primary place is usually a school.",
                "created_at": "2024-07-22T08:15:00Z",
                 "parent_reply_id": null, // Top-level reply
                 "child_replies_count": 0 // For threaded view
              },
              {
                 "id": 102,
                 "author": { "username": "another_helper", "preferred_name": "Thinker", "profile_picture_url": "..." },
                 "content": "Good point @Helper. Classroom is *within* the school, like an Operating Room is within a Hospital.",
                 "created_at": "2024-07-22T08:20:00Z",
                 "parent_reply_id": 101, // Reply to previous comment
                 "child_replies_count": 0
              }
              // ... other replies
            ]
          }
        }
        ```

*   **`POST /posts/{post_id}/replies/`**
    *   **Action:** Add a reply to a community post.
    *   **Permissions:** `IsSubscribed`
    *   **Request Body:**
        ```json
        {
          "content": "Thanks everyone, that makes more sense now!",
          "parent_reply_id": 102 // Optional ID of the reply being responded to (for threading)
        }
        ```
    *   **Success Response (201 Created):** Returns the newly created reply.
        ```json
        {
          "id": 103,
          "author": { "username": "current_user", ... },
          "content": "Thanks everyone, that makes more sense now!",
          "created_at": "2024-07-22T09:00:00Z",
          "parent_reply_id": 102
        }
        ```
    *   **Error Response (400 Bad Request):** If post is closed or parent reply doesn't exist.

*   **`GET /tags/`**
    *   **Action:** List popular or available tags for filtering/posting.
    *   **Permissions:** `IsSubscribed`
    *   **Success Response (200 OK):**
        ```json
        [
           { "name": "verbal", "slug": "verbal", "count": 150 }, // Count of posts with tag
           { "name": "quantitative", "slug": "quantitative", "count": 120 },
           { "name": "achievement", "slug": "achievement", "count": 80 },
           { "name": "tips", "slug": "tips", "count": 50 }
           // ...
        ]
        ```

---

**10. Admin Support (`/api/v1/support/`)**
<a name="admin-support"></a>

*   **`GET /tickets/`**
    *   **Action:** List the current user's support tickets.
    *   **Permissions:** `IsAuthenticated`
    *   **Query Parameters:** `status=open/closed`, `page`, `page_size`
    *   **Success Response (200 OK):** Paginated list.
        ```json
        {
          "count": 3,
          "next": null,
          "previous": null,
          "results": [
            {
              "id": 31,
              "subject": "Issue with Level Assessment score",
              "issue_type": "technical", // "technical", "financial", "question_problem", "other"
              "status": "pending_admin", // "open", "pending_admin", "pending_user", "closed"
              "created_at": "2024-07-20T14:00:00Z",
              "updated_at": "2024-07-21T10:00:00Z", // Last reply time
               "last_reply_by": "admin" // "user" or "admin"
            },
            {
              "id": 30,
              "subject": "Question #45 seems wrong",
              "issue_type": "question_problem",
              "status": "closed",
              "created_at": "2024-07-19T12:00:00Z",
              "updated_at": "2024-07-19T16:00:00Z",
               "last_reply_by": "admin"
            }
          ]
        }
        ```

*   **`POST /tickets/`**
    *   **Action:** Create a new support ticket.
    *   **Permissions:** `IsAuthenticated`
    *   **Request Body:** `multipart/form-data` if allowing attachments.
        *   `issue_type`: "question_problem"
        *   `subject`: "Incorrect explanation for Question #123" // Optional, can derive
        *   `description`: "The explanation provided for question ID 123 in the Algebra section doesn't seem correct based on the options."
        *   `attachment`: (optional file data - e.g., screenshot)
    *   **Success Response (201 Created):** Returns the created ticket details.
        ```json
        {
          "id": 32,
          "subject": "Incorrect explanation for Question #123",
          "issue_type": "question_problem",
          "status": "open",
          "created_at": "2024-07-22T15:00:00Z",
          "updated_at": "2024-07-22T15:00:00Z",
          "replies": [] // Starts empty
        }
        ```

*   **`GET /tickets/{ticket_id}/`**
    *   **Action:** Get details and replies for a specific support ticket.
    *   **Permissions:** `IsOwnerOrAdmin` (or `IsSubAdminWithPermission('view_support')`)
    *   **Success Response (200 OK):**
        ```json
        {
          "id": 31,
          "subject": "Issue with Level Assessment score",
          "issue_type": "technical",
          "status": "pending_admin",
          "description": "My level assessment score seems lower than expected...", // Initial user message
          "created_at": "2024-07-20T14:00:00Z",
          "updated_at": "2024-07-21T10:00:00Z",
          "replies": [
            {
              "id": 201,
              "user": { "username": "current_user", "preferred_name": "Ali", "role": "student" },
              "message": "My level assessment score seems lower than expected...", // Usually description is first message
              "is_internal_note": false, // Always false for user view
              "created_at": "2024-07-20T14:00:00Z"
            },
            {
              "id": 202,
              "user": { "username": "support_admin", "preferred_name": "Support", "role": "admin" },
              "message": "Thanks for reaching out, Ali. We are looking into your assessment attempt #123 now.",
              "is_internal_note": false,
              "created_at": "2024-07-21T10:00:00Z"
            }
            // ... other replies (excluding internal notes for student view)
          ]
        }
        ```

*   **`POST /tickets/{ticket_id}/replies/`**
    *   **Action:** Add a reply to a support ticket (by the user).
    *   **Permissions:** `IsOwnerOrAdmin` (or `IsSubAdminWithPermission('reply_support')`)
    *   **Request Body:**
        ```json
        {
          "message": "Thank you for checking!"
          // "is_internal_note" is only for admin endpoint
        }
        ```
    *   **Success Response (201 Created):** Returns the created reply.
        ```json
        {
          "id": 203,
          "user": { "username": "current_user", "preferred_name": "Ali", "role": "student" },
          "message": "Thank you for checking!",
          "is_internal_note": false,
          "created_at": "2024-07-22T16:00:00Z"
        }
        ```
    *   **Notes:** Updates `SupportTicket.status` (e.g., to 'pending_admin'), `updated_at`. Sends notification to assigned admin.

---

**11. Admin Panel (`/api/v1/admin/`)**
<a name="admin-panel"></a>

*These endpoints require `IsAdmin` or specific `IsSubAdminWithPermission(...)` permissions.*

*   **Sub-Admin Management:**
    *   `GET /sub-admins/`: List sub-admins.
    *   `POST /sub-admins/`: Create sub-admin (`username`, `email`, `password`, `full_name`, `account_type`, `permissions` list).
    *   `GET /sub-admins/{user_id}/`: Get details & permissions.
    *   `PATCH /sub-admins/{user_id}/`: Update details/permissions.
    *   `DELETE /sub-admins/{user_id}/`: Delete sub-admin account.
    *   `GET /permissions/`: List available permission choices.

*   **User Management:**
    *   `GET /users/`: List all users (students, admins) with filters (`search`, `role`, `is_active`).
    *   `GET /users/{user_id}/`: Get full profile, stats, activity log for a specific user.
    *   `PATCH /users/{user_id}/`: Modify user (`is_active`, `role`, subscription details - carefully!).
    *   `POST /users/{user_id}/reset-password/`: Trigger password reset email for a user.
    *   `POST /users/{user_id}/adjust-points/`: Add/remove points.
        *   Request: `{ "points_change": -50, "reason": "Manual correction for challenge issue." }`
        *   Response: `{ "user_id": N, "new_point_total": M }`

*   **Content Management (CMS-like functionality):**
    *   Endpoints for CRUD operations on `Page`, `FAQCategory`, `FAQItem`, `PartnerCategory`, `HomepageFeatureCard`, `HomepageStatistic`, `BlogPost`.
    *   Example: `PATCH /content/pages/{page_id}/` Request: `{ "title": "New Title", "content": "<p>Updated content</p>" }`

*   **Learning Content Management:**
    *   Endpoints for CRUD operations on `LearningSection`, `LearningSubSection`, `Skill`, `Question`.
    *   Example: `POST /learning/questions/` Request: (Full question data including `correct_answer`, `explanation`).

*   **Contact Messages:**
    *   `GET /contact-messages/`: List messages with filters (`status=new/read/replied`).
    *   `GET /contact-messages/{message_id}/`: Get message details.
    *   `POST /contact-messages/{message_id}/reply/`: Send reply. Request: `{ "response": "Thank you..." }`. Updates status to 'replied'.
    *   `PATCH /contact-messages/{message_id}/`: Update status (e.g., `{"status": "archived"}`).

*   **Admin Statistics & Export:**
    *   `GET /statistics/overview/`: Get aggregated platform stats (active users, test completions, avg scores, popular sections). Needs query params for date range, grouping.
    *   `GET /statistics/export/`: Trigger data export (e.g., user list, test results). Needs query params for format, filters. Likely triggers an async task (Celery). Response: `{ "task_id": "...", "message": "Export started. You will be notified upon completion." }`

*   **Serial Codes:**
    *   `GET /serial-codes/`: List codes with filters (`is_used`, `is_active`).
    *   `POST /serial-codes/`: Generate new codes. Request: `{ "count": 50, "duration_days": 30, "notes": "Batch for School X" }`.
    *   `PATCH /serial-codes/{code_id}/`: Update code (e.g., `{"is_active": false}`).

*   **Admin Support Ticket Management:**
    *   `GET /support/tickets/all/`: List *all* support tickets with filters (`status`, `assigned_to`, `issue_type`).
    *   `GET /support/tickets/{ticket_id}/admin/`: View ticket including internal notes.
    *   `POST /support/tickets/{ticket_id}/replies/admin/`: Add admin reply or internal note. Request: `{ "message": "...", "is_internal_note": true/false }`.
    *   `PATCH /support/tickets/{ticket_id}/admin/`: Assign ticket, change status/priority. Request: `{ "assigned_to": user_id, "status": "closed", "priority": 3 }`.
