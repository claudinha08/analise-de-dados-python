SELECT 
	product_id,
	product_name,
	categories.category_id,
	unit_price,
	category_name
FROM public.products
LEFT JOIN public.categories
	ON products.category_id = categories.category_id;
