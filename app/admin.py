from app.models import Room, RoomType, UserRole, RoomTypeRegulation, CustomerTypeRegulation, Receipt, SurchargeRegulation
from flask_admin import Admin, BaseView, expose, AdminIndexView
from app import app, db
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request
import dao
from datetime import datetime

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return (current_user.is_authenticated and
                current_user.role == UserRole.ADMIN)


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self):
        return current_user.is_authenticated


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        role_admin = None
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            role_admin = 'ADMIN'
        monthSaleStatistic = [
            (7, 10, 3000000, "2023-01-19 17:01:00", 1),
            (7, 8, 5000000, "2023-01-29 17:11:00", 2),
            (7, 9, 5000000, "2023-02-19 17:11:00", 3),
            (7, 10, 5000000, "2023-04-29 17:11:00", 4),
            (7, 10, 3000000, "2023-01-19 17:01:00", 6),
            (7, 1, 5000000, "2023-01-29 17:11:00", 7),
            (7, 2, 5000000, "2023-02-19 17:11:00", 8),
            (7, 3, 5000000, "2023-04-29 17:11:00", 9),
            (7, 4, 4000000, "2024-01-29 17:11:00", 10),
            (7, 5, 4000000, "2024-02-29 17:11:00", 11)
        ]
        return self.render('admin/index.html',
                           room_regulation=dao.get_room_type_regulation(),
                           customer_type_regulation=dao.get_customer_type_regulation(),
                           role_admin=role_admin, monthSaleStatistic=monthSaleStatistic,)



class MonthSaleStatisticView(BaseView):
    @expose('/')
    def index(self):
        kw = request.args.get('kw')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        month = request.args.get('month')
        year = request.args.get('year')

        mss = dao.month_sale_statistic(kw=kw,
                                       from_date=from_date,
                                       to_date=to_date,
                                       month=month,
                                       year=year)
        total_revenue = 0
        for m in mss:
            total_revenue = total_revenue + m[1]

        if not month:
            month = '(1-12)'
        if not year:
            year = '(All)'

        return self.render('admin/monthSaleStatistic.html',
                           monthSaleStatistic=mss,
                           total_revenue=total_revenue,
                           year=year,
                           month=month)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class MyRoomTypeView(AuthenticatedModelView):
    column_searchable_list = ['name']
    column_filters = ['name']
    column_editable_list = ['name']
    can_export = True
    can_view_details = True
    column_display_pk = True
    column_labels = {
        'name': 'Loại phòng',
        'rooms': 'Danh sách Phòng'
    }
    column_list = ['name', 'rooms']


class MyRoomView(AuthenticatedModelView):
    column_searchable_list = ['name']
    column_filters = ['name', 'room_type']
    column_editable_list = ['name', 'image']
    can_export = True
    can_view_details = True
    column_display_pk = True
    column_labels = {
        'name': 'Phòng',
        'room_type': 'Loại Phòng',
        'image': 'Ảnh Phòng'
    }
    column_list = ['name', 'image', 'room_type']


admin = Admin(app=app,
              name='Apolo Hotel Admin',
              template_mode='bootstrap4',
              index_view=MyAdminIndexView())


class MyRoomTypeRegulation(AuthenticatedModelView):
    column_searchable_list = ['room_type_id']
    column_filters = ['room_type_id', 'room_quanity', 'price']
    column_editable_list = ['room_quanity', 'price']
    can_view_details = True
    column_display_pk = True
    column_labels = {
        'room_type_id': 'Mã Loại phòng',
        'room_quanity': 'Số lượng phòng tối đa',
        'price': 'Đơn giá'
    }
    column_list = ['room_type_id', 'room_quanity', 'price']


class MyCustomerTypeRegulation(AuthenticatedModelView):
    column_filters = ['customer_type', 'rate']
    column_editable_list = ['rate']
    can_export = True
    can_view_details = True
    column_display_pk = True
    column_labels = {
        'rate': 'Hệ số khách nước ngoài',
        'capacity': 'Số lượng khách tối đa'
    }
    column_list = ['customer_type', 'rate']
class MySurchargeRegulation(AuthenticatedModelView):
    column_list = ['created_date', 'surcharge_rate', 'default_customer_count']
    column_labels = {
        'created_date': 'Ngày tạo',
        'surcharge_rate': 'Mức phụ thu thêm 1 khách',
        'default_customer_count': 'Số lượng khách tối đa 1 phòng'
    }
    can_export = True
    can_view_details = True
    column_display_pk = True

class MyReceipt(AuthenticatedModelView):
    column_list = ['id', 'total_price', 'receptionist_id', 'rental_room_id']
    column_filters = ['created_date', 'rental_room_id']


class RoomUtilizationReportView(BaseView):
    @expose('/')
    def index(self):
        name = request.args.get('name')
        month = request.args.get('month')
        year = request.args.get('year')

        room_utilization_report = dao.room_utilization_report(name=name, month=month, year=year)

        return self.render('admin/RoomUtilizationReport.html',
                           room_utilization_report=room_utilization_report)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

admin.add_view(MyRoomTypeView(RoomType, db.session, name='Loại phòng'))
admin.add_view(MyRoomView(Room, db.session, name='Danh sách phòng'))
admin.add_view(MyRoomTypeRegulation(RoomTypeRegulation, db.session, name='Quy định phòng'))
admin.add_view(MyCustomerTypeRegulation(CustomerTypeRegulation, db.session, name='Quy định loại khách hàng'))
admin.add_view(MySurchargeRegulation(SurchargeRegulation, db.session, name='Quy định Phụ thu'))
admin.add_view(MonthSaleStatisticView(name='Báo cáo-thống kê'))
admin.add_view(RoomUtilizationReportView(name='Báo cáo mật độ sử dụng phòng'))
admin.add_view(MyReceipt(Receipt, db.session, name='Hóa đơn'))
