# Product Design

## Positioning

Smart Tour Guide is an attraction/school recommendation system plus a campus-internal navigation demo for 北京邮电大学沙河校区. It emphasizes destination recommendation explainability, real campus map data, graph routing, diary/community interaction, food discovery, and admin visibility.

## Target Users

- Visitor: searches attractions/schools, selects a destination, finds diaries and food information.
- Student/staff: uses campus-internal map, food recommendation, and route planning repeatedly.
- Admin/demo operator: checks data scale, OSM import status, and feature readiness.

## Core User Flows

1. Open home dashboard and inspect recommended attractions/schools.
2. Search attractions/schools by name, category, or keyword.
3. Select a school/campus context, then open map guide and view internal roads, buildings, and facilities.
4. Plan an internal campus route and inspect distance/time/steps.
5. Query nearby facilities by category and graph distance.
6. Browse, publish, rate, and comment on diaries.
7. Recommend foods by cuisine, rating, heat, and distance.
8. Generate mock AIGC diary/storyboard output.
9. Check admin data scale and map import status.

## Demo Boundary

The system is optimized for course demonstration. Authentication, moderation editing, production RBAC, and real external AIGC calls remain future work.
