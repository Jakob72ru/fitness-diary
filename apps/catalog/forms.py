from django import forms
from .models import Product
from decimal import Decimal


class ProductWeightForm(forms.Form):
    weight = forms.DecimalField(
        label='',
        max_digits=6,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control weight-input-no-spin',
            'min': '0',
            'step': '0.01'
        }),
        initial=Decimal('1.00')  # пример значения по умолчанию
    )

    def clean_weight(self):
        w = self.cleaned_data.get('weight')
        if w in (None, ''):
            # вернуть значение по умолчанию из initial
            return self.fields['weight'].initial
        return w


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['id']


class UserWeightForm(forms.Form):
    user_weight = forms.DecimalField(label='',
                                     min_value=1,
                                     required=False,
                                     widget=forms.NumberInput(attrs={
                                         'class': 'form-control weight-user-input-no-spin'}),
                                     )


class CreateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('title', 'proteins', 'fats', 'carbohydrates', 'calories', 'weight', 'thumbnail')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control product-attribute'})


class UpdateProductForm(CreateProductForm):
    class Meta:
        model = Product
        fields = CreateProductForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control product-attribute'})


class SearchForm(forms.Form):
    query = forms.CharField()

