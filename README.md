<!-- 
for MYSQL 
INSERT INTO lab_individualtestresult (value, status, entered_by_id, individual_test_id, test_request_id, result_date, notes) 
VALUES (123, 'low', 4, 2, '2025-09-08 10:00:00','')
ON DUPLICATE KEY UPDATE 
    value = VALUES(value),
    status = VALUES(status),
    entered_by_id = VALUES(entered_by_id),
    result_date = VALUES(result_date),
    notes = VALUES(notes);
    
     -->

<!-- 
SQLite / PostgreSQL
INSERT INTO lab_individualtestresult (value, status, entered_by_id, individual_test_id, test_request_id, result_date, notes) 
VALUES (123, 'low', 4, 2, 2, '2025-09-08 10:00:00','')
ON CONFLICT(test_request_id, individual_test_id)
DO UPDATE SET 
    value = excluded.value,
    status = excluded.status,
    entered_by_id = excluded.entered_by_id,
    result_date = excluded.result_date,
    notes = excluded.notes;
 -->



## Contact

For support, feedback, or inquiries, please contact haderf119@gmail.com.

---

Thank you for choosing the Django Blog project. I hope you find this documentation helpful in exploring and using my application. If you have any questions or feedback, please don't hesitate to reach out. Happy blogging!