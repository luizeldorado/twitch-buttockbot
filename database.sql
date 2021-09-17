create table channels (
	id serial,
	twitch_name text,
	activated boolean default FALSE not null,
	frequency integer default 1 not null,
	probability double precision default 30 not null
);