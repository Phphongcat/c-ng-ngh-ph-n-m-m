from datetime import datetime

from flask import session, request
from flask_admin import Admin, expose, BaseView, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from wtforms import TextAreaField
from wtforms.widgets import TextArea
from cnpmapp import app, db, utils
from cnpmapp.models import Pricing, Category, Room, AccountRole


class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class AuthenticateBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role is AccountRole.ADMIN


class AuthenticateModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role is AccountRole.ADMIN


class PricingView(AuthenticateModelView):
    column_list = ['name', 'cost_cap', 'surcharge', 'abroad_coefficient', 'domestic_coefficient', 'rooms']
    column_exclude_list = ['image']
    column_labels = {
        'name': 'Tên',
        'cost_cap': 'Số người miễn phụ thu',
        'surcharge': 'Tỉ lệ phụ thu',
        'abroad_coefficient': 'Hệ số ngoại quốc',
        'domestic_coefficient': 'Hệ số nội quốc',
        'rooms': 'Phòng phụ thuộc'
    }


class CategoryView(AuthenticateModelView):
    pass


class RoomView(AuthenticateModelView):
    can_view_details = True
    column_exclude_list = ['image']
    column_searchable_list = ['name', 'cost']
    column_labels = {
        'name': 'Tên phòng',
        'cost': 'Giá',
        'description': 'Mô tả',
        'active': 'Trạng thái'
    }
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']
    form_overrides = {
        'description': CKTextAreaField
    }


class StatsView(AuthenticateBaseView):
    @expose('/')
    def index(self):
        m_kw = request.args.get('month-select')
        y_kw = request.args.get('year-select')
        month_kw = int(m_kw) if m_kw else datetime.now().month
        year_kw = int(y_kw) if y_kw else datetime.now().year

        return self.render('admin/stats.html',
                           month_kw=month_kw, year_kw=year_kw,
                           pricing_stats=utils.pricing_stats(month_kw, year_kw),
                           density_stats=utils.density_stats(month_kw, year_kw))


class RegisterView(AuthenticateBaseView):
    @expose('/')
    def index(self):
        keyword = 'register_message'
        m_error = None
        m_success = None

        if session.get(keyword):
            m_error = 'Lỗi hệ thống.' if session[keyword].__eq__('sys_error') else m_error
            m_error = 'Mật khẩu không khớp, yêu cầu nhập lại.' if session[keyword].__eq__('pass_error') else m_error
            m_success = 'Đăng kí tài khoản thành công' if session[keyword].__eq__('success') else m_success
            del session[keyword]

        return self.render('admin/register.html', m_error=m_error, m_success=m_success)


class AdminView(AdminIndexView):
    @expose('/')
    def index(self):
        if current_user.is_authenticated and current_user.role != AccountRole.ADMIN:
            logout_user()
        return self.render('admin/index.html')


admin = Admin(app, name='CNPM-Quản lý khách sạn', index_view=AdminView())
admin.add_view(PricingView(Pricing, db.session))
admin.add_view(CategoryView(Category, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(StatsView(name='Thống kê'))
admin.add_view(RegisterView(name='Tạo tài khoản'))
