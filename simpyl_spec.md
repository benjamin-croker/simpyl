# simpyl spec

## Description
[https://github.com/benjamin-croker/simpyl](https://github.com/benjamin-croker/simpyl)

## Concepts
* There is a hierarchy of environment -> run -> procedure
* A run is the result of calling several procedures (Python functions). The arguments are set and return values recorded for each procedure.
* Runs are performed in an environment. Basically environments exist to separate cache files, as they will be overwritten within an environment
logs are just text files stored on the directory
arguments to procedures can be entered manually or loaded from cache
results of procedures are stored as text, or if the procedure caches its return values, the filenames of the cached files are stored

## JSON Models


```
	environment:
	{
	  “name”:             		string
	}
	argument:
	{
	  “name”:           	 	string,
	  “value”:            		string,
	  “from_cache”:        		boolean
	}
	proc_init:
	{
	  “proc_name”:        		string,
	  “run_order”:        		number,
	  “?arguments”:        		Array.of(argument)    
	}
	run_init:
	{
	  “description”:          	string,
	  “environment_name”:    	string,
	  “?proc_inits”:        	Array.of(proc_init)
	}
	
	run_result:
	{
	  “id”:             		number,
	  “timestamp_start:			number,
	  “timestamp_stop:        	number,
	  “status”:            		string,
	  “description”:          	string,
	  “environment_name”:    	string,
	  “?proc_results”:        	Array.of(proc_call)
	}
	
	proc_result:
	{
	  “id”:            			number
	  “proc_name”:        		string,
	  “run_order”:        		number,
	  “timestamp_start”:    	number,
	  “timestamp_stop”:    		number,
	  “result”:            		string,
	  “run_result_id”:         string,
	  “?arguments”:        		Array.of(argument)    
	}
```

## API URLs
Get the list of environments. Returns a list of environment models

	/api/envs/                    [GET]

Add a new environment. POST data includes an environment JSON model

	/api/newenv/                    [POST]

Get a list of available procedure calls. Returns a list of available proc_init models

	/api/proc_inits/                [GET]

Get a list of runs performed in the given environment. Returns a list of JSON objects:

```
	{
  		“id”:            number,
  		“description”:          string,
  		“URL”:            string #api URL to get the run data
	}
```

	/api/<env_name>/runs            [GET]

Get the specified run model. Returns a run model
	
	/api/runs/<run_id>                [GET]

Start a new run/ POST data includes a run_init JSON model
	
	/api/newrun                    [POST]

Get the log file from the given run and environment. Returns text
	
	/api/<env_name>/<run_id>/log        [GET]

Database Tables

    CREATE TABLE environment (
        name TEXT PRIMARY KEY
    );

    CREATE TABLE run_result (
        id INTEGER PRIMARY KEY,
        timestamp_start REAL,
        timestamp_stop REAL,
        description TEXT,
        status TEXT,
        environment_name TEXT,
        FOREIGN KEY environment_name REFERENCES enviromnent(name)
    );

    CREATE TABLE cachefile (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        procedure_call_id INTEGER,
        FOREIGN KEY procedure_call_id REFERENCES procedure_call(id)
    );

    CREATE TABLE proc_result (
        id INTEGER PRIMARY KEY,
        proc_name TEXT,
        run_order INTEGER,
        timestamp_start REAL,
        timestamp_stop REAL,
        result TEXT,
        arguments TEXT,
        run_id INTEGER,
        FOREIGN KEY run_id REFERENCES run(id)
    );

