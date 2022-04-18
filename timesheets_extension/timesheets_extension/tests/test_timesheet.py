from odoo.tests import common


class TestCap(common.TransactionCase):
    def setUp(self):
        super(TestCap, self).setUp()

    def test_timesheet1(self):
        print('unit test 1')
        test_1 = self.env['account.analytic.line'].create({
            'project_id': int(2),
            'unit_amount': 1,
            'task_id': int(19),
            'name': 'unit test 1',
        })
        print(f'test1 is = to {test_1}')
        print("test is successful")

    def test_timesheet2(self):
        print('unit test 2')
        test_2 = self.env['account.analytic.line'].create({
            'project_id': int(2),
            'work_type': 'personal_effort',
            'unit_amount': 2,
            'task_id': int(16),
            'name': 'unit test 2',
        })
        print(f'test2 is = to {test_2}')
        print("test is successful")
        test_2.action_validate_state()
        print(test_2['state'])
        print('successfully validated')

    def test_timesheet3(self):
        print('unit test 3')
        test_3 = self.env['account.analytic.line'].create({
            'project_id': int(2),
            'work_type': 'requested_project_manager',
            'unit_amount': 3,
            'task_id': int(30),
            'name': 'unit test 3',
        })
        print(f'test3 is = to {test_3}')
        print("test is successful")
        test_3.action_refuse_validation_state()
        print(test_3['state'])
        print('successfully refused')
        test_3.action_reset_validation_state()
        print(test_3['state'])
        print('successfully reset to draft')
