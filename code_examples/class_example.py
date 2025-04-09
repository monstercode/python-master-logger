from master_logger.master_logger import Logger

logger = Logger()

class ClassExample:

    def method_example(self, param_example):
        logger.debug(param_example)
        return True

    @classmethod
    def classmethod_example(cls, param_example):
        logger.debug(param_example)
        return True

    @staticmethod
    def staticmethod_example(param_example):
        logger.debug(param_example)
        return True


example = ClassExample()
example.method_example("This is an example param for an instance")
ClassExample.classmethod_example("This is an example param for a class method")
ClassExample.staticmethod_example("This is a static method. We are not aware of the Class because it's static")

# This example showcases how we get the context of the log, from which Class and method or class method
# would be auto set to the log, so we can know where was it logged exactly from.
# [2025-04-08 16:21:14][DEBUG][ClassExample][method_example:8] This is an example param for an instance
# [2025-04-08 16:21:14][DEBUG][ClassExample][classmethod_example:13] This is an example param for a class method

# Static methods are not aware of what class they are defined in, so we can't autodetect
# the class, but still know the function name called. If necessary, pass the class name in the log manually
# [2025-04-08 16:21:14][DEBUG][staticmethod_example:18] This is a static method. We are not aware of the Class because it's static

